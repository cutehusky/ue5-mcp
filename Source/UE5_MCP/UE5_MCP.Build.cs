// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class UE5_MCP : ModuleRules
{
	public UE5_MCP(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;
		// Dense single-line editor utilities reuse short local names (E, F, Object) in nested scopes.
		CppCompileWarningSettings.ShadowVariableWarningLevel = WarningLevel.Off;
		
		PublicIncludePaths.AddRange(
			new string[] {
				// ... add public include paths required here ...
			}
			);
				
		
		PrivateIncludePaths.AddRange(
			new string[] {
				// ... add other private include paths required here ...
			}
			);
			
		
		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"Engine"
				// ... add other public dependencies that you statically link with here ...
			}
			);
			
		
		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"CoreUObject",
				"Projects",
				"InputCore",
				"EditorFramework",
				"UnrealEd",
				"ToolMenus",
				"Engine",
				"NavigationSystem",
                "Landscape",
                "Foliage",
                "PhysicsCore",
				"Json",
				"JsonUtilities",
				"Slate",
				"SlateCore", 
				"AssetTools",
                "ImageCore",
                "VirtualTexturingEditor",
				"SourceControl",
				"AssetRegistry",
				"MessageLog",
				"ContentBrowser",
				"DataLayerEditor",
                "WorldPartitionEditor",
				"AssetDefinition",
				"AssetManagerEditor",
				"BlueprintEditorLibrary",
				"BlueprintGraph",
                "MovieSceneTools",
                "Sequencer",
                "LevelSequenceEditor",
                "TakesCore",
                "GameFeatures",
                "SmartObjectsModule",
                "Blutility",
				"BlueprintFileUtils",
				"GraphEditor",
				"UMG",
				"UMGEditor",
				"AnimGraph",
				"AnimationBlueprintLibrary",
				"SkeletalMeshEditor",
				"StaticMeshEditor",
				"MaterialEditor",
				"Kismet",       
				"KismetCompiler",
				"HTTPServer",
                "HTTP",
				"Sockets",
				"RHI",
				"EnhancedInput",
				"InputEditor",
				"AIModule",
				"StateTreeModule",
				"PropertyBindingUtils",
				"StateTreeEditorModule",
				"GameplayStateTreeModule",
				"EnvironmentQueryEditor",
				"GameplayTags",
                "EngineSettings", "ApplicationCore",
                "RemoteControl",
                "GameplayAbilities",
                "GameplayTasks",
                "GameplayTagsEditor",
				"BehaviorTreeEditor",
				"AIGraph",
				"AudioEditor",
				"AudioMixer",
				"TraceLog",
				"AudioModulation",
				"AudioExtensions",
				"WaveTable",
				"AudioLinkCore",
				"MetasoundEngine",
				"MetasoundFrontend",
				"MetasoundEditor",
				"LevelSequence",
				"MovieScene",
				"MovieSceneTracks",
				"UniversalObjectLocator",
				"CinematicCamera",
				"PhysicsUtilities",
				"PoseSearch",
                "GeometryCore",
                "GeometryFramework",
                "GeometryScriptingCore",
                "PCG",
                "PCGEditor",
                "Niagara",
                "NiagaraEditor",
                "PoseSearchEditor",
                "IKRig",
                "IKRigEditor",
				"ControlRig",
				"ControlRigDeveloper",
				"RigVM",
				"RigVMDeveloper",
				"GameProjectGeneration",
				// ... add private dependencies that you statically link with here ...	
			}
			);
		
		
		if (Target.Platform == UnrealTargetPlatform.Win64)
		{
			PrivateDependencyModuleNames.Add("LiveCoding");
		}

		DynamicallyLoadedModuleNames.AddRange(
			new string[]
			{
				// ... add any modules that your module loads dynamically here ...
			}
			);
	}
}
