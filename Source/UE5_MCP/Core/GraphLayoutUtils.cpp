#include "GraphLayoutUtils.h"

#include "EdGraph/EdGraph.h"
#include "EdGraphNode_Comment.h"
#include "EdGraphSchema_K2.h"
#include "Engine/Blueprint.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "ScopedTransaction.h"
#include "Serialization/JsonWriter.h"

#include <stdexcept>

namespace
{
	constexpr double PinRowHeight = 24, HeaderHeight = 40, CommentPadding = 32, CommentHeader = 48, GridSnap = 16;
	constexpr double ExecWeight = 8;  // Execution wires matter most: keep them straight.

	struct FBox2 { double X, Y, W, H; };

	struct FWire
	{
		int32 From, To;              // Node indexes, output to input.
		double FromPinY, ToPinY;     // Pin height within the node.
		double Weight;
	};

	struct FItem                     // A node, or a dummy that carries a long wire through a column.
	{
		int32 Node = INDEX_NONE;
		double Width = 0, Height = 0, Y = 0;
		int32 Layer = 0;
	};

	struct FSegment { int32 From, To; double FromPinY, ToPinY, Weight; };

	double PinY(const UEdGraphNode* Node, const UEdGraphPin* Target)
	{
		int32 Row = 0;
		for (const UEdGraphPin* Pin : Node->Pins)
		{
			if (Pin == Target) break;
			if (Pin && !Pin->bHidden && Pin->Direction == Target->Direction) ++Row;
		}
		return HeaderHeight + PinRowHeight * (Row + 0.5);
	}

	// Real sizes come from editor widgets, which headless editors don't have, so estimate from the title and pins.
	FVector2D EstimateSize(const UEdGraphNode* Node)
	{
		int32 Inputs = 0, Outputs = 0;
		double InputText = 0, OutputText = 0;
		for (const UEdGraphPin* Pin : Node->Pins)
		{
			if (!Pin || Pin->bHidden) continue;
			double Text = Node->GetPinDisplayName(Pin).ToString().Len() * 7.0;
			if (Pin->Direction == EGPD_Input)
			{
				++Inputs;
				if (Pin->LinkedTo.IsEmpty() && Pin->PinType.PinCategory != UEdGraphSchema_K2::PC_Exec) Text += 70;  // Default value box.
				InputText = FMath::Max(InputText, Text);
			}
			else
			{
				++Outputs;
				OutputText = FMath::Max(OutputText, Text);
			}
		}
		const double Title = Node->GetNodeTitle(ENodeTitleType::ListView).ToString().Len() * 8.0 + 56;
		return FVector2D(FMath::Max3(120.0, Title, InputText + OutputText + 72), HeaderHeight + PinRowHeight * FMath::Max(Inputs, Outputs) + 12);
	}

	bool HasExecPin(const UEdGraphNode* Node)
	{
		for (const UEdGraphPin* Pin : Node->Pins)
			if (Pin && Pin->PinType.PinCategory == UEdGraphSchema_K2::PC_Exec) return true;
		return false;
	}

	// Least-squares positions that keep the order and the gaps: pool adjacent blocks that would otherwise overlap.
	void PlaceInOrder(const TArray<int32>& Column, TArray<FItem>& Items, const TArray<double>& Wanted, const TArray<double>& Strength, double Gap)
	{
		struct FBlock { double Sum, Weight; int32 Count; };
		TArray<double> Offset;
		double Running = 0;
		for (int32 Index : Column) { Offset.Add(Running); Running += Items[Index].Height + Gap; }
		TArray<FBlock> Blocks;
		for (int32 I = 0; I < Column.Num(); ++I)
		{
			Blocks.Add({(Wanted[I] - Offset[I]) * Strength[I], Strength[I], 1});
			while (Blocks.Num() > 1)
			{
				const FBlock& B = Blocks.Last();
				const FBlock& A = Blocks[Blocks.Num() - 2];
				if (A.Sum / A.Weight <= B.Sum / B.Weight) break;
				const FBlock Merged{A.Sum + B.Sum, A.Weight + B.Weight, A.Count + B.Count};
				Blocks.Pop();
				Blocks.Last() = Merged;
			}
		}
		int32 I = 0;
		for (const FBlock& Block : Blocks)
			for (int32 K = 0; K < Block.Count; ++K, ++I) Items[Column[I]].Y = Block.Sum / Block.Weight + Offset[I];
	}

	int64 CountLayerCrossings(const TArray<TArray<int32>>& Columns, const TArray<FSegment>& Segments, const TArray<FItem>& Items)
	{
		TArray<int32> Rank;
		Rank.SetNumZeroed(Items.Num());
		for (const TArray<int32>& Column : Columns)
			for (int32 I = 0; I < Column.Num(); ++I) Rank[Column[I]] = I;
		TArray<TArray<const FSegment*>> ByLayer;
		ByLayer.SetNum(Columns.Num());
		for (const FSegment& S : Segments) ByLayer[Items[S.From].Layer].Add(&S);
		int64 Total = 0;
		for (const TArray<const FSegment*>& Layer : ByLayer)
			for (int32 A = 0; A < Layer.Num(); ++A)
				for (int32 B = A + 1; B < Layer.Num(); ++B)
					if ((Rank[Layer[A]->From] - Rank[Layer[B]->From]) * (Rank[Layer[A]->To] - Rank[Layer[B]->To]) < 0) ++Total;
		return Total;
	}

	// Lays out one connected component. Node positions are returned relative to its top left.
	FVector2D LayoutComponent(const TArray<int32>& Members, const TArray<FWire>& Wires, const TArray<UEdGraphNode*>& Nodes, const TArray<FVector2D>& Sizes,
		double ColumnSpacing, double RowSpacing, TArray<FVector2D>& OutPositions)
	{
		TMap<int32, int32> Local;
		for (int32 I = 0; I < Members.Num(); ++I) Local.Add(Members[I], I);
		const int32 Count = Members.Num();
		TArray<FWire> Edges;
		for (const FWire& Wire : Wires)
			if (Local.Contains(Wire.From) && Local.Contains(Wire.To))
				Edges.Add({Local[Wire.From], Local[Wire.To], Wire.FromPinY, Wire.ToPinY, Wire.Weight});

		// Walk from the event-like nodes, along execution wires first. A wire back to a node on the current path closes a cycle.
		TArray<TArray<int32>> Out;
		TArray<int32> InCount;
		Out.SetNum(Count);
		InCount.SetNumZeroed(Count);
		for (int32 E = 0; E < Edges.Num(); ++E) { Out[Edges[E].From].Add(E); ++InCount[Edges[E].To]; }
		for (TArray<int32>& List : Out)
			List.StableSort([&Edges](int32 A, int32 B) { return Edges[A].Weight != Edges[B].Weight ? Edges[A].Weight > Edges[B].Weight : Edges[A].FromPinY < Edges[B].FromPinY; });
		TArray<int32> Roots;
		for (int32 I = 0; I < Count; ++I) Roots.Add(I);
		Roots.StableSort([&](int32 A, int32 B)
		{
			const bool RootA = InCount[A] == 0 && HasExecPin(Nodes[Members[A]]), RootB = InCount[B] == 0 && HasExecPin(Nodes[Members[B]]);
			if (RootA != RootB) return RootA;
			if ((InCount[A] == 0) != (InCount[B] == 0)) return InCount[A] == 0;
			return Nodes[Members[A]]->NodePosY < Nodes[Members[B]]->NodePosY;
		});
		TArray<uint8> State;
		State.SetNumZeroed(Count);
		TArray<int32> Visit;
		Visit.SetNumZeroed(Count);
		TArray<bool> Backward;
		Backward.SetNumZeroed(Edges.Num());
		int32 Clock = 0;
		for (int32 Root : Roots)
		{
			if (State[Root]) continue;
			TArray<TPair<int32, int32>> Stack;  // Explicit, so a long chain can't overflow the call stack.
			Stack.Add({Root, 0});
			State[Root] = 1;
			Visit[Root] = Clock++;
			while (!Stack.IsEmpty())
			{
				TPair<int32, int32>& Top = Stack.Last();
				if (Top.Value >= Out[Top.Key].Num()) { State[Top.Key] = 2; Stack.Pop(); continue; }
				const int32 E = Out[Top.Key][Top.Value++];
				const int32 To = Edges[E].To;
				if (State[To] == 1) Backward[E] = true;
				else if (State[To] == 0) { State[To] = 1; Visit[To] = Clock++; Stack.Add({To, 0}); }
			}
		}

		// Columns: longest path from the start, then pull pure nodes next to whatever uses them.
		TArray<int32> Layer, Pending, Order;
		Layer.SetNumZeroed(Count);
		Pending.SetNumZeroed(Count);
		TArray<TArray<int32>> Next, Prev;
		Next.SetNum(Count);
		Prev.SetNum(Count);
		for (int32 E = 0; E < Edges.Num(); ++E)
		{
			const int32 A = Backward[E] ? Edges[E].To : Edges[E].From, B = Backward[E] ? Edges[E].From : Edges[E].To;
			Next[A].Add(B);
			Prev[B].Add(A);
			++Pending[B];
		}
		for (int32 I = 0; I < Count; ++I) if (Pending[I] == 0) Order.Add(I);
		for (int32 Head = 0; Head < Order.Num(); ++Head)
			for (int32 B : Next[Order[Head]])
			{
				Layer[B] = FMath::Max(Layer[B], Layer[Order[Head]] + 1);
				if (--Pending[B] == 0) Order.Add(B);
			}
		for (int32 Index = Order.Num() - 1; Index >= 0; --Index)
		{
			const int32 I = Order[Index];
			if (Next[I].IsEmpty() || HasExecPin(Nodes[Members[I]])) continue;
			int32 Nearest = MAX_int32;
			for (int32 B : Next[I]) Nearest = FMath::Min(Nearest, Layer[B]);
			Layer[I] = Nearest - 1;
		}
		int32 Lowest = MAX_int32, Highest = 0;
		for (int32 I = 0; I < Count; ++I) Lowest = FMath::Min(Lowest, Layer[I]);
		for (int32 I = 0; I < Count; ++I) { Layer[I] -= Lowest; Highest = FMath::Max(Highest, Layer[I]); }

		// Items: real nodes, plus a dummy in every column a long wire passes through.
		TArray<FItem> Items;
		TArray<double> Seed;
		for (int32 I = 0; I < Count; ++I)
		{
			FItem Item;
			Item.Node = I;
			Item.Width = Sizes[Members[I]].X;
			Item.Height = Sizes[Members[I]].Y;
			Item.Layer = Layer[I];
			Items.Add(Item);
			Seed.Add(Visit[I]);
		}
		TArray<FSegment> Segments;
		for (int32 E = 0; E < Edges.Num(); ++E)
		{
			const FWire& Wire = Edges[E];
			const bool bFlip = Backward[E];
			const int32 A = bFlip ? Wire.To : Wire.From, B = bFlip ? Wire.From : Wire.To;
			const double APin = bFlip ? Wire.ToPinY : Wire.FromPinY, BPin = bFlip ? Wire.FromPinY : Wire.ToPinY;
			int32 Previous = A;
			double PreviousPin = APin;
			for (int32 L = Layer[A] + 1; L < Layer[B]; ++L)
			{
				FItem Dummy;
				Dummy.Height = PinRowHeight;
				Dummy.Layer = L;
				const int32 Added = Items.Add(Dummy);
				Seed.Add(double(Seed[A]));  // A copy: the array may reallocate.
				Segments.Add({Previous, Added, PreviousPin, PinRowHeight / 2, Wire.Weight});
				Previous = Added;
				PreviousPin = PinRowHeight / 2;
			}
			Segments.Add({Previous, B, PreviousPin, BPin, Wire.Weight});
		}
		TArray<TArray<const FSegment*>> Left, Right;
		Left.SetNum(Items.Num());
		Right.SetNum(Items.Num());
		for (const FSegment& S : Segments) { Right[S.From].Add(&S); Left[S.To].Add(&S); }

		// Row order: sweep back and forth by the average position of neighbours, and keep the best order seen.
		TArray<TArray<int32>> Columns;
		Columns.SetNum(Highest + 1);
		for (int32 I = 0; I < Items.Num(); ++I) Columns[Items[I].Layer].Add(I);
		for (TArray<int32>& Column : Columns) Column.StableSort([&Seed](int32 A, int32 B) { return Seed[A] < Seed[B]; });
		TArray<TArray<int32>> Best = Columns;
		int64 BestCrossings = CountLayerCrossings(Columns, Segments, Items);
		TArray<double> Rank;
		Rank.SetNumZeroed(Items.Num());
		const auto Reset = [&]() { for (const TArray<int32>& C : Columns) for (int32 I = 0; I < C.Num(); ++I) Rank[C[I]] = I; };
		for (int32 Sweep = 0; Sweep < 16 && BestCrossings > 0; ++Sweep)
		{
			const bool bForward = Sweep % 2 == 0;
			for (int32 Step = 1; Step < Columns.Num(); ++Step)
			{
				TArray<int32>& Column = Columns[bForward ? Step : Columns.Num() - 1 - Step];
				Reset();
				TMap<int32, double> Score;
				for (int32 I : Column)
				{
					double Sum = 0, Weight = 0;
					for (const FSegment* S : (bForward ? Left : Right)[I])
					{
						const int32 Other = bForward ? S->From : S->To;
						const double OtherPin = (bForward ? S->FromPinY : S->ToPinY) / 1000.0;
						Sum += (Rank[Other] + OtherPin) * S->Weight;
						Weight += S->Weight;
					}
					Score.Add(I, Weight > 0 ? Sum / Weight : Rank[I]);
				}
				Column.StableSort([&Score](int32 A, int32 B) { return Score[A] < Score[B]; });
			}
			const int64 Crossings = CountLayerCrossings(Columns, Segments, Items);
			if (Crossings < BestCrossings) { BestCrossings = Crossings; Best = Columns; }
		}
		Columns = Best;

		// Rows: repeatedly move nodes to line their pins up with their neighbours, ending with a pass from the start.
		for (TArray<int32>& Column : Columns)
		{
			double Running = 0;
			for (int32 I : Column) { Items[I].Y = Running; Running += Items[I].Height + RowSpacing; }
		}
		for (int32 Pass = 0; Pass < 12; ++Pass)
		{
			const bool bForward = Pass % 2 == 1;
			for (int32 Step = 1; Step < Columns.Num(); ++Step)
			{
				const TArray<int32>& Column = Columns[bForward ? Step : Columns.Num() - 1 - Step];
				TArray<double> Wanted, Strength;
				for (int32 I : Column)
				{
					double Sum = 0, Weight = 0;
					for (const FSegment* S : (bForward ? Left : Right)[I])
					{
						Sum += ((bForward ? Items[S->From].Y + S->FromPinY - S->ToPinY : Items[S->To].Y + S->ToPinY - S->FromPinY)) * S->Weight;
						Weight += S->Weight;
					}
					Wanted.Add(Weight > 0 ? Sum / Weight : Items[I].Y);
					Strength.Add(Weight > 0 ? Weight : 0.01);
				}
				PlaceInOrder(Column, Items, Wanted, Strength, RowSpacing);
			}
		}

		double Top = TNumericLimits<double>::Max(), Bottom = TNumericLimits<double>::Lowest(), X = 0;
		for (const FItem& Item : Items)
			if (Item.Node != INDEX_NONE) { Top = FMath::Min(Top, Item.Y); Bottom = FMath::Max(Bottom, Item.Y + Item.Height); }
		for (const TArray<int32>& Column : Columns)
		{
			double Width = 0;
			for (int32 I : Column)
				if (Items[I].Node != INDEX_NONE)
				{
					OutPositions[Members[Items[I].Node]] = FVector2D(X, Items[I].Y - Top);
					Width = FMath::Max(Width, Items[I].Width);
				}
			X += Width + ColumnSpacing;
		}
		return FVector2D(FMath::Max(0.0, X - ColumnSpacing), Bottom - Top);
	}

	struct FMetrics { int32 Crossings = 0, Overlaps = 0; };

	FMetrics Measure(const TArray<FBox2>& Boxes, const TArray<FWire>& Wires)
	{
		FMetrics Result;
		for (int32 A = 0; A < Boxes.Num(); ++A)
			for (int32 B = A + 1; B < Boxes.Num(); ++B)
				if (Boxes[A].X < Boxes[B].X + Boxes[B].W && Boxes[B].X < Boxes[A].X + Boxes[A].W && Boxes[A].Y < Boxes[B].Y + Boxes[B].H && Boxes[B].Y < Boxes[A].Y + Boxes[A].H) ++Result.Overlaps;
		if (Wires.Num() > 2000) return Result;
		const auto Side = [](double Ax, double Ay, double Bx, double By, double Cx, double Cy) { return (Bx - Ax) * (Cy - Ay) - (By - Ay) * (Cx - Ax); };
		for (int32 I = 0; I < Wires.Num(); ++I)
			for (int32 K = I + 1; K < Wires.Num(); ++K)
			{
				const FWire& P = Wires[I];
				const FWire& Q = Wires[K];
				if (P.From == Q.From || P.To == Q.To || P.From == Q.To || P.To == Q.From) continue;
				const double Ax = Boxes[P.From].X + Boxes[P.From].W, Ay = Boxes[P.From].Y + P.FromPinY, Bx = Boxes[P.To].X, By = Boxes[P.To].Y + P.ToPinY;
				const double Cx = Boxes[Q.From].X + Boxes[Q.From].W, Cy = Boxes[Q.From].Y + Q.FromPinY, Dx = Boxes[Q.To].X, Dy = Boxes[Q.To].Y + Q.ToPinY;
				if (Side(Ax, Ay, Bx, By, Cx, Cy) * Side(Ax, Ay, Bx, By, Dx, Dy) < 0 && Side(Cx, Cy, Dx, Dy, Ax, Ay) * Side(Cx, Cy, Dx, Dy, Bx, By) < 0) ++Result.Crossings;
			}
		return Result;
	}
}

FString GraphLayoutUtils::Format(UBlueprint* Blueprint, UEdGraph* Graph, const TArray<FString>& NodeIds, int32 ColumnSpacing, int32 RowSpacing, bool bDryRun)
{
	if (!Blueprint || !Graph) throw std::runtime_error("A Blueprint and graph are required");
	if (ColumnSpacing < 0 || ColumnSpacing > 2000 || RowSpacing < 0 || RowSpacing > 2000) throw std::runtime_error("column_spacing and row_spacing must be 0-2000");

	TSet<FGuid> Wanted;
	for (const FString& Id : NodeIds)
	{
		FGuid Guid;
		if (!FGuid::Parse(Id, Guid)) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("%s is not a node id. get_graph lists the node ids."), *Id)));
		Wanted.Add(Guid);
	}
	TArray<UEdGraphNode*> Nodes;
	TArray<UEdGraphNode_Comment*> Comments;
	for (UEdGraphNode* Node : Graph->Nodes)
	{
		if (!Node) continue;
		if (UEdGraphNode_Comment* Comment = Cast<UEdGraphNode_Comment>(Node)) Comments.Add(Comment);
		else if (Wanted.IsEmpty() || Wanted.Contains(Node->NodeGuid)) Nodes.Add(Node);
	}
	if (!Wanted.IsEmpty() && Nodes.Num() != Wanted.Num()) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Found %d of the %d node ids in graph %s. get_graph lists the node ids; comments can't be listed."), Nodes.Num(), Wanted.Num(), *Graph->GetName())));
	Nodes.StableSort([](const UEdGraphNode& A, const UEdGraphNode& B) { return A.NodePosY != B.NodePosY ? A.NodePosY < B.NodePosY : A.NodeGuid < B.NodeGuid; });

	TMap<const UEdGraphNode*, int32> Index;
	TArray<FVector2D> Sizes;
	for (int32 I = 0; I < Nodes.Num(); ++I) { Index.Add(Nodes[I], I); Sizes.Add(EstimateSize(Nodes[I])); }
	TArray<FWire> Wires;
	TArray<int32> Group;
	for (int32 I = 0; I < Nodes.Num(); ++I) Group.Add(I);
	const TFunction<int32(int32)> Find = [&Group, &Find](int32 I) { return Group[I] == I ? I : Group[I] = Find(Group[I]); };
	for (int32 I = 0; I < Nodes.Num(); ++I)
		for (const UEdGraphPin* Pin : Nodes[I]->Pins)
		{
			if (!Pin || Pin->Direction != EGPD_Output) continue;
			for (const UEdGraphPin* Linked : Pin->LinkedTo)
			{
				const int32* To = Linked ? Index.Find(Linked->GetOwningNode()) : nullptr;
				if (!To || *To == I) continue;
				Wires.Add({I, *To, PinY(Nodes[I], Pin), PinY(Nodes[*To], Linked), Pin->PinType.PinCategory == UEdGraphSchema_K2::PC_Exec ? ExecWeight : 1.0});
				Group[Find(I)] = Find(*To);
			}
		}

	TArray<FBox2> Before, After;
	double OriginX = TNumericLimits<double>::Max(), OriginY = TNumericLimits<double>::Max();
	for (int32 I = 0; I < Nodes.Num(); ++I)
	{
		Before.Add({(double)Nodes[I]->NodePosX, (double)Nodes[I]->NodePosY, Sizes[I].X, Sizes[I].Y});
		OriginX = FMath::Min(OriginX, Before[I].X);
		OriginY = FMath::Min(OriginY, Before[I].Y);
	}

	// Connected groups stack vertically, largest first, from where the graph already starts.
	TMap<int32, TArray<int32>> Components;
	for (int32 I = 0; I < Nodes.Num(); ++I) Components.FindOrAdd(Find(I)).Add(I);
	TArray<TArray<int32>> Ordered;
	for (TPair<int32, TArray<int32>>& Pair : Components) Ordered.Add(Pair.Value);
	Ordered.StableSort([](const TArray<int32>& A, const TArray<int32>& B) { return A.Num() != B.Num() ? A.Num() > B.Num() : A[0] < B[0]; });
	TArray<FVector2D> Positions;
	Positions.SetNumZeroed(Nodes.Num());
	double NextY = 0, TotalWidth = 0;
	for (const TArray<int32>& Members : Ordered)
	{
		const FVector2D Bounds = LayoutComponent(Members, Wires, Nodes, Sizes, ColumnSpacing, RowSpacing, Positions);
		for (int32 I : Members) Positions[I].Y += NextY;
		NextY += Bounds.Y + RowSpacing * 3;
		TotalWidth = FMath::Max(TotalWidth, Bounds.X);
	}
	for (int32 I = 0; I < Nodes.Num(); ++I)
	{
		Positions[I].X = FMath::GridSnap(Positions[I].X + (Nodes.IsEmpty() ? 0 : OriginX), GridSnap);
		Positions[I].Y = FMath::GridSnap(Positions[I].Y + (Nodes.IsEmpty() ? 0 : OriginY), GridSnap);
		After.Add({Positions[I].X, Positions[I].Y, Sizes[I].X, Sizes[I].Y});
	}
	const FMetrics MetricsBefore = Measure(Before, Wires), MetricsAfter = Measure(After, Wires);

	// A comment keeps the nodes it contained, as long as all of them are being moved.
	struct FCommentFit { UEdGraphNode_Comment* Comment; TArray<int32> Members; };
	TArray<FCommentFit> Fits;
	int32 CommentsLeft = 0;
	for (UEdGraphNode_Comment* Comment : Comments)
	{
		FCommentFit Fit{Comment, {}};
		bool bAllMoving = true;
		for (UEdGraphNode* Node : Graph->Nodes)
		{
			if (!Node || Cast<UEdGraphNode_Comment>(Node)) continue;
			const FVector2D Size = EstimateSize(Node);
			const double CenterX = Node->NodePosX + Size.X / 2, CenterY = Node->NodePosY + Size.Y / 2;
			if (CenterX < Comment->NodePosX || CenterY < Comment->NodePosY || CenterX > Comment->NodePosX + Comment->NodeWidth || CenterY > Comment->NodePosY + Comment->NodeHeight) continue;
			if (const int32* Found = Index.Find(Node)) Fit.Members.Add(*Found);
			else bAllMoving = false;
		}
		if (bAllMoving && !Fit.Members.IsEmpty()) Fits.Add(MoveTemp(Fit));
		else ++CommentsLeft;
	}

	FString Json;
	const TSharedRef<TJsonWriter<>> J = TJsonWriterFactory<>::Create(&Json);
	J->WriteObjectStart();
	J->WriteValue(TEXT("graph"), Graph->GetName());
	J->WriteValue(TEXT("dry_run"), bDryRun);
	J->WriteValue(TEXT("nodes"), Nodes.Num());
	J->WriteValue(TEXT("wires"), Wires.Num());
	J->WriteValue(TEXT("groups"), Ordered.Num());
	J->WriteValue(TEXT("width"), TotalWidth);
	J->WriteValue(TEXT("height"), FMath::Max(0.0, NextY - RowSpacing * 3));
	J->WriteValue(TEXT("crossings_before"), MetricsBefore.Crossings);
	J->WriteValue(TEXT("crossings_after"), MetricsAfter.Crossings);
	J->WriteValue(TEXT("overlaps_before"), MetricsBefore.Overlaps);
	J->WriteValue(TEXT("overlaps_after"), MetricsAfter.Overlaps);
	J->WriteValue(TEXT("comments_resized"), Fits.Num());
	J->WriteValue(TEXT("comments_left_in_place"), CommentsLeft);
	J->WriteValue(TEXT("note"), TEXT("Sizes are estimated, because headless editors have no node widgets. Crossings count straight lines between pins."));
	J->WriteArrayStart(TEXT("positions"));
	for (int32 I = 0; I < Nodes.Num(); ++I)
	{
		J->WriteObjectStart();
		J->WriteValue(TEXT("node_id"), Nodes[I]->NodeGuid.ToString());
		J->WriteValue(TEXT("title"), Nodes[I]->GetNodeTitle(ENodeTitleType::ListView).ToString());
		J->WriteValue(TEXT("x"), (int32)Positions[I].X);
		J->WriteValue(TEXT("y"), (int32)Positions[I].Y);
		J->WriteObjectEnd();
	}
	J->WriteArrayEnd();
	J->WriteObjectEnd();
	J->Close();

	if (!bDryRun && !Nodes.IsEmpty())
	{
		const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "FormatGraph", "Format Graph"));
		for (int32 I = 0; I < Nodes.Num(); ++I)
		{
			Nodes[I]->Modify();
			Nodes[I]->NodePosX = (int32)Positions[I].X;
			Nodes[I]->NodePosY = (int32)Positions[I].Y;
		}
		for (const FCommentFit& Fit : Fits)
		{
			double Left = TNumericLimits<double>::Max(), Top = Left, Right = TNumericLimits<double>::Lowest(), Bottom = Right;
			for (int32 I : Fit.Members)
			{
				Left = FMath::Min(Left, After[I].X);
				Top = FMath::Min(Top, After[I].Y);
				Right = FMath::Max(Right, After[I].X + After[I].W);
				Bottom = FMath::Max(Bottom, After[I].Y + After[I].H);
			}
			Fit.Comment->Modify();
			Fit.Comment->NodePosX = (int32)(Left - CommentPadding);
			Fit.Comment->NodePosY = (int32)(Top - CommentHeader);
			Fit.Comment->NodeWidth = (int32)(Right - Left + CommentPadding * 2);
			Fit.Comment->NodeHeight = (int32)(Bottom - Top + CommentHeader + CommentPadding);
		}
		Graph->NotifyGraphChanged();
		FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);
	}
	return Json;
}
