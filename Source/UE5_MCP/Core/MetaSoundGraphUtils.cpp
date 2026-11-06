#include "MetaSoundGraphUtils.h"

#include "UE5_MCP/API/DTO/MetaSoundCreateReq.h"
#include "UE5_MCP/API/DTO/MetaSoundGraphReq.h"

#include "AssetToolsModule.h"
#include "Editor.h"
#include "Misc/PackageName.h"
#include "Metasound.h"
#include "MetasoundBuilderBase.h"
#include "MetasoundEditorSubsystem.h"
#include "MetasoundFactory.h"
#include "MetasoundFrontendDocument.h"
#include "MetasoundFrontendDocumentBuilder.h"
#include "MetasoundFrontendNodeClassRegistry.h"
#include "MetasoundSource.h"
#include "Modules/ModuleManager.h"
#include "ScopedTransaction.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "UObject/UnrealType.h"

#include "Serialization/JsonWriter.h"

#include <stdexcept>

namespace
{
	TScriptInterface<IMetaSoundDocumentInterface> AsMetaSoundDocument(UObject* Asset)
	{
		TScriptInterface<IMetaSoundDocumentInterface> Document = Asset;
		if (!Asset || !Document.GetObject()) throw std::runtime_error("Asset is not a MetaSound source or patch");
		return Document;
	}

	UMetaSoundBuilderBase* FindBuilder(UObject* Asset)
	{
		TScriptInterface<IMetaSoundDocumentInterface> Document = AsMetaSoundDocument(Asset);
		UMetaSoundEditorSubsystem* EditorSubsystem = GEditor ? GEditor->GetEditorSubsystem<UMetaSoundEditorSubsystem>() : nullptr;
		if (!EditorSubsystem) throw std::runtime_error("MetaSound Editor Subsystem is unavailable");
		EMetaSoundBuilderResult Result = EMetaSoundBuilderResult::Failed;
		UMetaSoundBuilderBase* Builder = EditorSubsystem->FindOrBeginBuilding(Document, Result);
		if (!Builder || Result != EMetaSoundBuilderResult::Succeeded) throw std::runtime_error("Could not begin building the MetaSound document");
		return Builder;
	}

	UEditorAssetSubsystem* GetAssetSubsystem()
	{
		UEditorAssetSubsystem* Subsystem = GEditor ? GEditor->GetEditorSubsystem<UEditorAssetSubsystem>() : nullptr;
		if (!Subsystem) throw std::runtime_error("Editor Asset Subsystem is unavailable");
		return Subsystem;
	}

	void SaveIfRequested(UObject* Asset, bool bSave)
	{
		if (bSave && (!Asset || !GetAssetSubsystem()->SaveAsset(Asset->GetPathName(), true)))
			throw std::runtime_error("Failed to save MetaSound asset");
	}

	FString GuidString(const FGuid& Guid)
	{
		return Guid.ToString(EGuidFormats::DigitsWithHyphens);
	}

	FGuid ParseGuid(const FString& Text, const TCHAR* FieldName)
	{
		FGuid Guid;
		if (!FGuid::Parse(Text, Guid))
			throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("%s must be a valid MetaSound node GUID"), FieldName)));
		return Guid;
	}

	FString InputTypeString(const FName TypeName)
	{
		return TypeName.ToString();
	}

	bool FindRegisteredClass(const FMetasoundFrontendClassName& ClassName, int32 MajorVersion,
		FText* OutDisplayName = nullptr)
	{
		Metasound::Frontend::INodeClassRegistry* Registry = Metasound::Frontend::INodeClassRegistry::Get();
		if (!Registry) return false;
		bool bFound = false;
		Registry->IterateRegistry([&](const FMetasoundFrontendClass& RegisteredClass)
		{
			if (bFound || RegisteredClass.Metadata.GetType() != EMetasoundFrontendClassType::External) return;
			if (RegisteredClass.Metadata.GetClassName() != ClassName
				|| RegisteredClass.Metadata.GetVersion().Major != MajorVersion
				|| !EnumHasAnyFlags(RegisteredClass.Metadata.GetAccessFlags(), EMetasoundFrontendClassAccessFlags::Referenceable)) return;
			bFound = true;
#if WITH_EDITOR
			if (OutDisplayName) *OutDisplayName = RegisteredClass.Metadata.GetDisplayName();
#endif
		});
		return bFound;
	}

	bool MetaSoundPathExists(const FMetasoundFrontendGraph& Graph, const FGuid& Start, const FGuid& Goal)
	{
		TArray<FGuid> Pending;
		TSet<FGuid> Visited;
		Pending.Add(Start);
		while (!Pending.IsEmpty())
		{
			const FGuid Current = Pending.Pop(EAllowShrinking::No);
			if (Current == Goal) return true;
			if (Visited.Contains(Current)) continue;
			Visited.Add(Current);
			for (const FMetasoundFrontendEdge& Edge : Graph.Edges)
				if (Edge.FromNodeID == Current && !Visited.Contains(Edge.ToNodeID)) Pending.Add(Edge.ToNodeID);
		}
		return false;
	}

	FString GraphActionJson(UObject* Asset, const FString& Operation, const FString& NodeId,
		bool bChanged, bool bWouldChange, bool bDryRun, bool bSaved)
	{
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Asset->GetPathName());
		Writer->WriteValue(TEXT("operation"), Operation);
		Writer->WriteValue(TEXT("node_id"), NodeId);
		Writer->WriteValue(TEXT("changed"), bChanged);
		Writer->WriteValue(TEXT("would_change"), bWouldChange);
		Writer->WriteValue(TEXT("dry_run"), bDryRun);
		Writer->WriteValue(TEXT("saved"), bSaved);
		Writer->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty());
		Writer->WriteObjectEnd(); Writer->Close();
		return Json;
	}

	void WriteVertexArray(TSharedRef<TJsonWriter<>>& Writer, const TCHAR* Key,
		const TArray<FMetasoundFrontendVertex>& Vertices)
	{
		Writer->WriteArrayStart(Key);
		for (const FMetasoundFrontendVertex& Vertex : Vertices)
		{
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Vertex.Name.ToString());
			Writer->WriteValue(TEXT("type"), Vertex.TypeName.ToString());
			Writer->WriteValue(TEXT("vertex_id"), GuidString(Vertex.VertexID));
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
	}
}

namespace MetaSoundGraphUtils
{
	FString Create(const FMetaSoundCreateReq& Request)
	{
		if (!IsInGameThread()) throw std::runtime_error("MetaSound asset creation requires the editor game thread");
		if (Request.AssetPath.Contains(TEXT(".")) || !FPackageName::IsValidLongPackageName(Request.AssetPath, false))
			throw std::runtime_error("asset_path must be a valid long package name without an object suffix");
		const FString AssetType = Request.AssetType.TrimStartAndEnd().ToLower();
		if (AssetType != TEXT("source") && AssetType != TEXT("patch"))
			throw std::runtime_error("asset_type must be source or patch");
		UObject* Parent = nullptr;
		if (!Request.ParentAssetPath.IsEmpty())
		{
			Parent = StaticLoadObject(UObject::StaticClass(), nullptr, *Request.ParentAssetPath);
			if (!Parent) throw std::runtime_error("parent_asset_path was not found");
			if ((AssetType == TEXT("source") && !Parent->IsA<UMetaSoundSource>())
				|| (AssetType == TEXT("patch") && !Parent->IsA<UMetaSoundPatch>()))
				throw std::runtime_error("parent_asset_path must identify the same MetaSound type requested by asset_type");
		}
		FString UniquePackageName;
		FString UniqueAssetName;
		FAssetToolsModule& AssetTools = FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools"));
		AssetTools.Get().CreateUniqueAssetName(Request.AssetPath, TEXT(""), UniquePackageName, UniqueAssetName);
		const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *UniquePackageName, *UniqueAssetName);
		if (Request.bDryRun)
		{
			FString Json;
			TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("would_create"), true);
			Writer->WriteValue(TEXT("asset_path"), ObjectPath);
			Writer->WriteValue(TEXT("asset_type"), AssetType);
			Writer->WriteValue(TEXT("is_preset"), Parent != nullptr);
			Writer->WriteValue(TEXT("dry_run"), true);
			Writer->WriteObjectEnd(); Writer->Close();
			return Json;
		}
		UFactory* Factory = AssetType == TEXT("source")
			? static_cast<UFactory*>(NewObject<UMetaSoundSourceFactory>())
			: static_cast<UFactory*>(NewObject<UMetaSoundFactory>());
		if (Parent)
		{
			FObjectPropertyBase* ReferenceProperty = FindFProperty<FObjectPropertyBase>(Factory->GetClass(), FName(TEXT("ReferencedMetaSoundObject")));
			if (!ReferenceProperty) throw std::runtime_error("MetaSound factory preset reference property is unavailable");
			ReferenceProperty->SetObjectPropertyValue_InContainer(Factory, Parent);
		}
		UClass* AssetClass = AssetType == TEXT("source") ? UMetaSoundSource::StaticClass() : UMetaSoundPatch::StaticClass();
		UObject* Asset = AssetTools.Get().CreateAsset(UniqueAssetName,
			FPackageName::GetLongPackagePath(UniquePackageName), AssetClass, Factory);
		if (!Asset) throw std::runtime_error("failed to create MetaSound asset");
		Asset->MarkPackageDirty();
		SaveIfRequested(Asset, Request.bSave);
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("created"), true);
		Writer->WriteValue(TEXT("asset_path"), Asset->GetPathName());
		Writer->WriteValue(TEXT("asset_type"), AssetType);
		Writer->WriteValue(TEXT("is_preset"), Parent != nullptr);
		Writer->WriteValue(TEXT("saved"), Request.bSave);
		Writer->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty());
		Writer->WriteObjectEnd(); Writer->Close();
		return Json;
	}

	FString NodeClasses(const FString& Search, int32 Limit)
	{
		const FString Needle = Search.TrimStartAndEnd();
		const int32 MaxResults = FMath::Clamp(Limit, 1, 500);
		Metasound::Frontend::INodeClassRegistry* Registry = Metasound::Frontend::INodeClassRegistry::Get();
		if (!Registry) throw std::runtime_error("MetaSound node class registry is unavailable");
		TArray<const FMetasoundFrontendClass*> Matches;
		Registry->IterateRegistry([&](const FMetasoundFrontendClass& Class)
		{
			const FMetasoundFrontendClassMetadata& Metadata = Class.Metadata;
			if (Metadata.GetType() != EMetasoundFrontendClassType::External
				|| !EnumHasAnyFlags(Metadata.GetAccessFlags(), EMetasoundFrontendClassAccessFlags::Referenceable)) return;
			const FMetasoundFrontendClassName& Name = Metadata.GetClassName();
			if (!Needle.IsEmpty() && !Name.ToString().Contains(Needle, ESearchCase::IgnoreCase)
				&& !Metadata.GetDisplayName().ToString().Contains(Needle, ESearchCase::IgnoreCase)) return;
			Matches.Add(&Class);
		});
		Matches.Sort([](const FMetasoundFrontendClass& A, const FMetasoundFrontendClass& B)
		{
			return A.Metadata.GetClassName().ToString() < B.Metadata.GetClassName().ToString();
		});
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("search"), Needle);
		Writer->WriteValue(TEXT("limit"), MaxResults);
		Writer->WriteArrayStart(TEXT("node_classes"));
		int32 Count = 0;
		for (const FMetasoundFrontendClass* Class : Matches)
		{
			if (Count++ >= MaxResults) break;
			const FMetasoundFrontendClassMetadata& Metadata = Class->Metadata;
			const FMetasoundFrontendClassName& Name = Metadata.GetClassName();
			const FMetasoundFrontendVersionNumber& Version = Metadata.GetVersion();
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("class_name"), Name.ToString());
			Writer->WriteValue(TEXT("namespace"), Name.Namespace.ToString());
			Writer->WriteValue(TEXT("name"), Name.Name.ToString());
			Writer->WriteValue(TEXT("variant"), Name.Variant.ToString());
			Writer->WriteValue(TEXT("major_version"), Version.Major);
			Writer->WriteValue(TEXT("minor_version"), Version.Minor);
			Writer->WriteValue(TEXT("display_name"), Metadata.GetDisplayName().ToString());
			Writer->WriteValue(TEXT("description"), Metadata.GetDescription().ToString());
			Writer->WriteArrayStart(TEXT("inputs"));
			for (const FMetasoundFrontendClassInput& Input : Class->GetDefaultInterface().Inputs)
			{
				Writer->WriteObjectStart(); Writer->WriteValue(TEXT("name"), Input.Name.ToString());
				Writer->WriteValue(TEXT("type"), Input.TypeName.ToString()); Writer->WriteObjectEnd();
			}
			Writer->WriteArrayEnd();
			Writer->WriteArrayStart(TEXT("outputs"));
			for (const FMetasoundFrontendClassOutput& Output : Class->GetDefaultInterface().Outputs)
			{
				Writer->WriteObjectStart(); Writer->WriteValue(TEXT("name"), Output.Name.ToString());
				Writer->WriteValue(TEXT("type"), Output.TypeName.ToString()); Writer->WriteObjectEnd();
			}
			Writer->WriteArrayEnd();
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("total_matches"), Matches.Num());
		Writer->WriteObjectEnd(); Writer->Close();
		return Json;
	}

	FString Inspect(UObject* Asset)
	{
		TScriptInterface<IMetaSoundDocumentInterface> DocumentInterface = AsMetaSoundDocument(Asset);
		const FMetasoundFrontendDocument& Document = DocumentInterface->GetConstDocument();
		const FMetasoundFrontendGraphClass& Root = Document.RootGraph;
		const FMetasoundFrontendGraph& Graph = Root.GetConstDefaultGraph();
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Asset->GetPathName());
		Writer->WriteValue(TEXT("asset_type"), Asset->IsA<UMetaSoundSource>() ? TEXT("source") : TEXT("patch"));
		Writer->WriteValue(TEXT("is_preset"), Root.PresetOptions.bIsPreset);
		Writer->WriteValue(TEXT("class_name"), Root.Metadata.GetClassName().ToString());
		Writer->WriteValue(TEXT("class_version"), Root.Metadata.GetVersion().ToString());
		Writer->WriteValue(TEXT("display_name"), Root.Metadata.GetDisplayName().ToString());
		Writer->WriteValue(TEXT("description"), Root.Metadata.GetDescription().ToString());
		Writer->WriteArrayStart(TEXT("interfaces"));
		for (const FMetasoundFrontendVersion& Interface : Document.Interfaces) Writer->WriteValue(Interface.ToString());
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("graph_inputs"));
		for (const FMetasoundFrontendClassInput& Input : Root.GetDefaultInterface().Inputs)
		{
			Writer->WriteObjectStart(); Writer->WriteValue(TEXT("name"), Input.Name.ToString());
			Writer->WriteValue(TEXT("type"), Input.TypeName.ToString()); Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("graph_outputs"));
		for (const FMetasoundFrontendClassOutput& Output : Root.GetDefaultInterface().Outputs)
		{
			Writer->WriteObjectStart(); Writer->WriteValue(TEXT("name"), Output.Name.ToString());
			Writer->WriteValue(TEXT("type"), Output.TypeName.ToString()); Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("nodes"));
		for (const FMetasoundFrontendNode& Node : Graph.Nodes)
		{
			const FMetasoundFrontendClass* NodeClass = Document.Dependencies.FindByPredicate([&Node](const FMetasoundFrontendClass& Candidate)
			{
				return Candidate.ID == Node.ClassID;
			});
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("node_id"), GuidString(Node.GetID()));
			Writer->WriteValue(TEXT("node_name"), Node.Name.ToString());
			Writer->WriteValue(TEXT("class_id"), GuidString(Node.ClassID));
			Writer->WriteValue(TEXT("class_name"), NodeClass ? NodeClass->Metadata.GetClassName().ToString() : TEXT(""));
			Writer->WriteValue(TEXT("title"), NodeClass ? NodeClass->Metadata.GetDisplayName().ToString() : Node.Name.ToString());
			WriteVertexArray(Writer, TEXT("inputs"), Node.Interface.Inputs);
			WriteVertexArray(Writer, TEXT("outputs"), Node.Interface.Outputs);
			Writer->WriteArrayStart(TEXT("input_defaults"));
			for (const FMetasoundFrontendVertexLiteral& Literal : Node.InputLiterals)
			{
				Writer->WriteObjectStart(); Writer->WriteValue(TEXT("vertex_id"), GuidString(Literal.VertexID));
				Writer->WriteValue(TEXT("value"), Literal.Value.ToString()); Writer->WriteObjectEnd();
			}
			Writer->WriteArrayEnd();
#if WITH_EDITORONLY_DATA
			Writer->WriteArrayStart(TEXT("locations"));
			for (const auto& Location : Node.Style.Display.Locations)
			{
				Writer->WriteObjectStart(); Writer->WriteValue(TEXT("location_id"), GuidString(Location.Key));
				Writer->WriteValue(TEXT("x"), Location.Value.X); Writer->WriteValue(TEXT("y"), Location.Value.Y);
				Writer->WriteObjectEnd();
			}
			Writer->WriteArrayEnd();
#endif
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("edges"));
		for (const FMetasoundFrontendEdge& Edge : Graph.Edges)
		{
			Writer->WriteObjectStart(); Writer->WriteValue(TEXT("source_node_id"), GuidString(Edge.FromNodeID));
			Writer->WriteValue(TEXT("source_vertex_id"), GuidString(Edge.FromVertexID));
			Writer->WriteValue(TEXT("target_node_id"), GuidString(Edge.ToNodeID));
			Writer->WriteValue(TEXT("target_vertex_id"), GuidString(Edge.ToVertexID)); Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("node_count"), Graph.Nodes.Num());
		Writer->WriteValue(TEXT("edge_count"), Graph.Edges.Num());
		Writer->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty());
		Writer->WriteObjectEnd(); Writer->Close();
		return Json;
	}

	FString Mutate(UObject* Asset, const FMetaSoundGraphReq& Request)
	{
		AsMetaSoundDocument(Asset);
		UMetaSoundBuilderBase* Builder = FindBuilder(Asset);
		const FString Operation = Request.Operation.TrimStartAndEnd().ToLower();
		const FMetaSoundFrontendDocumentBuilder& ConstBuilder = Builder->GetConstBuilder();
		const FMetasoundFrontendGraph& Graph = ConstBuilder.GetConstDocumentChecked().RootGraph.GetConstDefaultGraph();
		FGuid NodeGuid;
		FMetaSoundNodeHandle NodeHandle;
		FGuid SourceGuid;
		FGuid TargetGuid;
		FMetaSoundNodeHandle SourceHandle;
		FMetaSoundNodeHandle TargetHandle;
		FMetaSoundBuilderNodeInputHandle InputHandle;
		FMetaSoundBuilderNodeOutputHandle OutputHandle;
		EMetaSoundBuilderResult Result = EMetaSoundBuilderResult::Failed;
		bool bWouldChange = false;
		bool bChanged = false;
		FString ResultNodeId = Request.NodeId;

		if (Operation == TEXT("add_node"))
		{
			FMetasoundFrontendClassName ClassName;
			if (!FMetasoundFrontendClassName::Parse(Request.NodeClass, ClassName) || !ClassName.IsValid() || Request.MajorVersion < 1)
				throw std::runtime_error("node_class must be a valid MetaSound class name from /metasounds/node-classes");
			if (!FindRegisteredClass(ClassName, Request.MajorVersion)) throw std::runtime_error("node_class and major_version do not identify a referenceable registered node");
			bWouldChange = true;
			if (!Request.bDryRun)
			{
				const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "AddMetaSoundNode", "Add MetaSound Node"));
				Asset->Modify();
				const FMetaSoundNodeHandle NewNode = Builder->AddNodeByClassName(ClassName, Result, Request.MajorVersion);
				if (Result != EMetaSoundBuilderResult::Succeeded || !NewNode.IsSet()) throw std::runtime_error("MetaSound builder rejected the node class");
				Builder->SetNodeLocation(NewNode, FVector2D(Request.PositionX, Request.PositionY), Result);
				if (Result != EMetaSoundBuilderResult::Succeeded) throw std::runtime_error("MetaSound builder could not assign node location");
				ResultNodeId = GuidString(NewNode.NodeID);
				bChanged = true;
			}
		}
		else if (Operation == TEXT("connect"))
		{
			SourceGuid = ParseGuid(Request.SourceNodeId, TEXT("source_node_id"));
			TargetGuid = ParseGuid(Request.TargetNodeId, TEXT("target_node_id"));
			SourceHandle = FMetaSoundNodeHandle(SourceGuid);
			TargetHandle = FMetaSoundNodeHandle(TargetGuid);
			if (!Builder->ContainsNode(SourceHandle) || !Builder->ContainsNode(TargetHandle)) throw std::runtime_error("source_node_id or target_node_id is not present in this MetaSound graph");
			OutputHandle = Builder->FindNodeOutputByName(SourceHandle, FName(*Request.SourceOutput), Result);
			if (Result != EMetaSoundBuilderResult::Succeeded || !OutputHandle.IsSet()) throw std::runtime_error("source_output does not identify an output on source_node_id");
			InputHandle = Builder->FindNodeInputByName(TargetHandle, FName(*Request.TargetInput), Result);
			if (Result != EMetaSoundBuilderResult::Succeeded || !InputHandle.IsSet()) throw std::runtime_error("target_input does not identify an input on target_node_id");
			FName OutputName; FName OutputType; FName InputName; FName InputType;
			Builder->GetNodeOutputData(OutputHandle, OutputName, OutputType, Result);
			if (Result != EMetaSoundBuilderResult::Succeeded) throw std::runtime_error("could not read source output metadata");
			Builder->GetNodeInputData(InputHandle, InputName, InputType, Result);
			if (Result != EMetaSoundBuilderResult::Succeeded) throw std::runtime_error("could not read target input metadata");
			if (OutputType != InputType) throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("MetaSound pin types do not match (%s to %s)"), *OutputType.ToString(), *InputType.ToString())));
			if (Builder->GetNodeOutputIsConstructorPin(OutputHandle) != Builder->GetNodeInputIsConstructorPin(InputHandle))
				throw std::runtime_error("MetaSound pin access types do not match");
			if (Builder->NodesAreConnected(OutputHandle, InputHandle))
				return GraphActionJson(Asset, Operation, Request.TargetNodeId, false, false, Request.bDryRun, false);
			const bool bInputConnected = Builder->NodeInputIsConnected(InputHandle);
			if (bInputConnected && !Request.bReplaceExisting) throw std::runtime_error("target_input is already connected; set replace_existing=true to replace it");
			if (MetaSoundPathExists(Graph, TargetGuid, SourceGuid)) throw std::runtime_error("connection would introduce a MetaSound graph cycle");
			bWouldChange = true;
			if (!Request.bDryRun)
			{
				const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "ConnectMetaSoundNodes", "Connect MetaSound Nodes"));
				Asset->Modify();
				if (bInputConnected)
				{
					Builder->DisconnectNodeInput(InputHandle, Result);
					if (Result != EMetaSoundBuilderResult::Succeeded) throw std::runtime_error("could not disconnect the previous input connection");
				}
				Builder->ConnectNodes(OutputHandle, InputHandle, Result);
				if (Result != EMetaSoundBuilderResult::Succeeded) throw std::runtime_error("MetaSound builder rejected the connection");
				bChanged = true;
			}
		}
		else if (Operation == TEXT("disconnect"))
		{
			SourceGuid = ParseGuid(Request.SourceNodeId, TEXT("source_node_id"));
			TargetGuid = ParseGuid(Request.TargetNodeId, TEXT("target_node_id"));
			SourceHandle = FMetaSoundNodeHandle(SourceGuid);
			TargetHandle = FMetaSoundNodeHandle(TargetGuid);
			OutputHandle = Builder->FindNodeOutputByName(SourceHandle, FName(*Request.SourceOutput), Result);
			if (Result != EMetaSoundBuilderResult::Succeeded || !OutputHandle.IsSet()) throw std::runtime_error("source_output was not found");
			InputHandle = Builder->FindNodeInputByName(TargetHandle, FName(*Request.TargetInput), Result);
			if (Result != EMetaSoundBuilderResult::Succeeded || !InputHandle.IsSet()) throw std::runtime_error("target_input was not found");
			bWouldChange = Builder->NodesAreConnected(OutputHandle, InputHandle);
			if (bWouldChange && !Request.bDryRun)
			{
				const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "DisconnectMetaSoundNodes", "Disconnect MetaSound Nodes"));
				Asset->Modify(); Builder->DisconnectNodes(OutputHandle, InputHandle, Result);
				if (Result != EMetaSoundBuilderResult::Succeeded) throw std::runtime_error("MetaSound builder rejected the disconnect");
				bChanged = true;
			}
		}
		else if (Operation == TEXT("remove_node"))
		{
			NodeGuid = ParseGuid(Request.NodeId, TEXT("node_id"));
			NodeHandle = FMetaSoundNodeHandle(NodeGuid);
			const FMetasoundFrontendNode* Node = ConstBuilder.FindNode(NodeGuid);
			if (!Node) throw std::runtime_error("node_id was not found");
			const FMetasoundFrontendClass* NodeClass = ConstBuilder.GetConstDocumentChecked().Dependencies.FindByPredicate([Node](const FMetasoundFrontendClass& Class)
			{
				return Class.ID == Node->ClassID;
			});
			if (NodeClass && (NodeClass->Metadata.GetType() == EMetasoundFrontendClassType::Input
				|| NodeClass->Metadata.GetType() == EMetasoundFrontendClassType::Output))
				throw std::runtime_error("MetaSound graph interface nodes cannot be removed with remove_node");
			bWouldChange = true;
			if (!Request.bDryRun && !Request.bConfirm) throw std::runtime_error("removing a MetaSound node requires confirm=true");
			if (!Request.bDryRun)
			{
				const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "RemoveMetaSoundNode", "Remove MetaSound Node"));
				Asset->Modify(); Builder->RemoveNode(NodeHandle, Result);
				if (Result != EMetaSoundBuilderResult::Succeeded) throw std::runtime_error("MetaSound builder rejected node removal");
				bChanged = true;
			}
		}
		else if (Operation == TEXT("set_input_default"))
		{
			NodeGuid = ParseGuid(Request.NodeId, TEXT("node_id"));
			NodeHandle = FMetaSoundNodeHandle(NodeGuid);
			InputHandle = Builder->FindNodeInputByName(NodeHandle, FName(*Request.InputName), Result);
			if (Result != EMetaSoundBuilderResult::Succeeded || !InputHandle.IsSet()) throw std::runtime_error("input_name was not found on node_id");
			FName VertexName; FName DataType;
			Builder->GetNodeInputData(InputHandle, VertexName, DataType, Result);
			if (Result != EMetaSoundBuilderResult::Succeeded) throw std::runtime_error("could not read MetaSound input type");
			FMetasoundFrontendLiteral Literal;
			if (DataType == TEXT("Float"))
			{
				float Value = 0.f;
				if (!LexTryParseString(Value, *Request.InputValue) || !FMath::IsFinite(Value)) throw std::runtime_error("Float input_value must be a finite number");
				Literal.Set(Value);
			}
			else if (DataType == TEXT("Int32"))
			{
				int32 Value = 0;
				if (!LexTryParseString(Value, *Request.InputValue)) throw std::runtime_error("Int32 input_value must be an integer");
				Literal.Set(Value);
			}
			else if (DataType == TEXT("Bool"))
			{
				if (Request.InputValue.Equals(TEXT("true"), ESearchCase::IgnoreCase)) Literal.Set(true);
				else if (Request.InputValue.Equals(TEXT("false"), ESearchCase::IgnoreCase)) Literal.Set(false);
				else throw std::runtime_error("Bool input_value must be true or false");
			}
			else if (DataType == TEXT("String")) Literal.Set(Request.InputValue);
			else throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("input defaults of MetaSound type %s are not supported by this route"), *DataType.ToString())));
			const FMetasoundFrontendLiteral Current = Builder->GetNodeInputDefault(InputHandle, Result);
			bWouldChange = Result != EMetaSoundBuilderResult::Succeeded || !Current.IsEqual(Literal);
			if (bWouldChange && !Request.bDryRun)
			{
				const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "SetMetaSoundInputDefault", "Set MetaSound Input Default"));
				Asset->Modify(); Builder->SetNodeInputDefault(InputHandle, Literal, Result);
				if (Result != EMetaSoundBuilderResult::Succeeded) throw std::runtime_error("MetaSound builder rejected the input default");
				bChanged = true;
			}
		}
		else if (Operation == TEXT("move_node"))
		{
			NodeGuid = ParseGuid(Request.NodeId, TEXT("node_id"));
			NodeHandle = FMetaSoundNodeHandle(NodeGuid);
			if (!Builder->ContainsNode(NodeHandle)) throw std::runtime_error("node_id was not found");
			const FMetasoundFrontendNode* Node = ConstBuilder.FindNode(NodeGuid);
			FVector2D CurrentLocation = FVector2D::ZeroVector;
#if WITH_EDITORONLY_DATA
			if (Node && !Node->Style.Display.Locations.IsEmpty()) CurrentLocation = Node->Style.Display.Locations.CreateConstIterator()->Value;
#endif
			bWouldChange = !FMath::IsNearlyEqual(CurrentLocation.X, static_cast<double>(Request.PositionX))
				|| !FMath::IsNearlyEqual(CurrentLocation.Y, static_cast<double>(Request.PositionY));
			if (bWouldChange && !Request.bDryRun)
			{
				const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "MoveMetaSoundNode", "Move MetaSound Node"));
				Asset->Modify(); Builder->SetNodeLocation(NodeHandle, FVector2D(Request.PositionX, Request.PositionY), Result);
				if (Result != EMetaSoundBuilderResult::Succeeded) throw std::runtime_error("MetaSound builder rejected the location");
				bChanged = true;
			}
		}
		else
		{
			throw std::runtime_error("operation must be add_node, connect, disconnect, remove_node, set_input_default, or move_node");
		}
		if (bChanged)
		{
			Asset->MarkPackageDirty();
			SaveIfRequested(Asset, Request.bSave);
		}
		return GraphActionJson(Asset, Operation, ResultNodeId.IsEmpty() ? Request.NodeId : ResultNodeId,
			bChanged, bWouldChange, Request.bDryRun, bChanged && Request.bSave);
	}

	FString Validate(UObject* Asset)
	{
		AsMetaSoundDocument(Asset);
		UMetaSoundBuilderBase* Builder = FindBuilder(Asset);
		const FMetaSoundFrontendDocumentBuilder& DocumentBuilder = Builder->GetConstBuilder();
		const FMetasoundFrontendDocument& Document = DocumentBuilder.GetConstDocumentChecked();
		const FMetasoundFrontendGraph& Graph = Document.RootGraph.GetConstDefaultGraph();
		TArray<FString> Errors;
		TArray<FString> Warnings;
		if (!DocumentBuilder.IsValid()) Errors.Add(TEXT("MetaSound frontend document builder reports an invalid document"));
		TSet<FGuid> NodeIds;
		for (const FMetasoundFrontendNode& Node : Graph.Nodes) NodeIds.Add(Node.GetID());
		for (const FMetasoundFrontendEdge& Edge : Graph.Edges)
		{
			if (!NodeIds.Contains(Edge.FromNodeID) || !NodeIds.Contains(Edge.ToNodeID))
				Errors.Add(TEXT("MetaSound edge references a missing node"));
			if (DocumentBuilder.IsValidEdge(Edge) != Metasound::Frontend::EInvalidEdgeReason::None)
				Errors.Add(TEXT("MetaSound edge has invalid pins, data types, access types, or connection cardinality"));
		}
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("asset_path"), Asset->GetPathName());
		Writer->WriteValue(TEXT("valid"), Errors.IsEmpty());
		Writer->WriteValue(TEXT("validation_scope"), TEXT("metasound_frontend_document_and_graph_edges"));
		Writer->WriteValue(TEXT("node_count"), Graph.Nodes.Num());
		Writer->WriteValue(TEXT("edge_count"), Graph.Edges.Num());
		Writer->WriteArrayStart(TEXT("errors")); for (const FString& Error : Errors) Writer->WriteValue(Error); Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("warnings")); for (const FString& Warning : Warnings) Writer->WriteValue(Warning); Writer->WriteArrayEnd();
		Writer->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty());
		Writer->WriteObjectEnd(); Writer->Close();
		return Json;
	}

	FString Compile(UObject* Asset, bool bDryRun, bool bSave)
	{
		AsMetaSoundDocument(Asset);
		UMetaSoundEditorSubsystem* EditorSubsystem = GEditor ? GEditor->GetEditorSubsystem<UMetaSoundEditorSubsystem>() : nullptr;
		if (!EditorSubsystem) throw std::runtime_error("MetaSound Editor Subsystem is unavailable");
		if (bDryRun)
		{
			FString Json;
			TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("would_compile"), true);
			Writer->WriteValue(TEXT("asset_path"), Asset->GetPathName());
			Writer->WriteValue(TEXT("dry_run"), true);
			Writer->WriteValue(TEXT("save_requested"), bSave);
			Writer->WriteObjectEnd(); Writer->Close();
			return Json;
		}
		EditorSubsystem->RegisterGraphWithFrontend(*Asset, true);
		UMetaSoundBuilderBase* Builder = FindBuilder(Asset);
		const bool bValid = Builder->GetConstBuilder().IsValid();
		UEdGraph* AssetGraph = nullptr;
		if (UMetaSoundSource* Source = Cast<UMetaSoundSource>(Asset)) AssetGraph = Source->GetGraph();
		else if (UMetaSoundPatch* Patch = Cast<UMetaSoundPatch>(Asset)) AssetGraph = Patch->GetGraph();
		UMetasoundEditorGraphBase* EditorGraph = Cast<UMetasoundEditorGraphBase>(AssetGraph);
		const int32 MessageSeverity = EditorGraph ? EditorGraph->GetHighestMessageSeverity() : 0;
		const bool bSaved = bSave && bValid;
		if (bSaved) SaveIfRequested(Asset, true);
		FString Json;
		TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("compiled"), bValid);
		Writer->WriteValue(TEXT("valid"), bValid);
		Writer->WriteValue(TEXT("asset_path"), Asset->GetPathName());
		Writer->WriteValue(TEXT("save_requested"), bSave);
		Writer->WriteValue(TEXT("saved"), bSaved);
		Writer->WriteValue(TEXT("dirty"), Asset->GetOutermost()->IsDirty());
		Writer->WriteValue(TEXT("editor_graph_available"), EditorGraph != nullptr);
		if (EditorGraph) Writer->WriteValue(TEXT("message_severity"), MessageSeverity);
		else Writer->WriteNull(TEXT("message_severity"));
		Writer->WriteObjectEnd(); Writer->Close();
		return Json;
	}
}
