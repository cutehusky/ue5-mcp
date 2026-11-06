#pragma once
#include "CoreMinimal.h"
#include "WorldSettingsReq.generated.h"

USTRUCT()
struct FWorldSettingsColorBytes
{
    GENERATED_BODY()
    UPROPERTY() int32 R = 0;
    UPROPERTY() int32 G = 0;
    UPROPERTY() int32 B = 0;
    UPROPERTY() int32 A = 255;
};

USTRUCT()
struct FWorldNavigationSettings
{
	GENERATED_BODY()
	/** Empty keeps the stored config class. Supported native config classes are inspected. */
	UPROPERTY() FString ConfigClass;
	UPROPERTY() bool bSetSystemClass = false;
	UPROPERTY() FString SystemClass;
	UPROPERTY() bool bSetSupportedAgents = false;
	UPROPERTY() TArray<int32> SupportedAgentIndices;
	UPROPERTY() bool bSetDefaultAgentName = false;
	UPROPERTY() FString DefaultAgentName;
	UPROPERTY() TMap<FString, bool> BoolSettings;
};

USTRUCT()
struct FWorldSettingsReq
{
	GENERATED_BODY()
	/** Optional stale-world guard: exact active persistent map package. */
	UPROPERTY() FString WorldPath;
	UPROPERTY() FString TilePackagePath;
	UPROPERTY() FString LayerName;
	UPROPERTY() FString ExpectedLayerName;
	UPROPERTY() bool bDistanceStreamingEnabled = false;
	UPROPERTY() bool bExpectedDistanceStreamingEnabled = false;
	UPROPERTY() int32 ExpectedTileCount = -1;
	UPROPERTY() int32 ExpectedLODCount = -1;
	UPROPERTY() TArray<int32> LODDistances;
	UPROPERTY() TArray<int32> ExpectedLODDistances;
	UPROPERTY() FString CompositionPath;
	UPROPERTY() TArray<double> ColorValues;
	UPROPERTY() TArray<double> ExpectedColorValues;
	UPROPERTY() TArray<int32> PairValues;
	UPROPERTY() TArray<int32> ExpectedPairValues;
	UPROPERTY() FString Name;
	UPROPERTY() FString ExpectedName;
	UPROPERTY() FString ObjectPath;
	UPROPERTY() FString ExpectedObjectPath;
	UPROPERTY() FString ExpectedLevelText;
	UPROPERTY() TArray<FString> ExpectedLevelTexts;
	UPROPERTY() TArray<int32> LevelOrder;
	UPROPERTY() int32 LevelIndex = -1;
	UPROPERTY() FString FieldName;
	UPROPERTY() double Value = 0;
	UPROPERTY() double ExpectedValue = 0;
	UPROPERTY() int32 Start = 0;
	UPROPERTY() int32 Count = 64;
	UPROPERTY() TMap<FString, FTransform> TransformSettings;
	UPROPERTY() TMap<FString, FTransform> ExpectedTransformSettings;
	UPROPERTY() TMap<FString, double> ExpectedNumericSettings;
	UPROPERTY() TMap<FString, bool> ExpectedBoolSettings;
	UPROPERTY() TMap<FString, FString> ExpectedClassSettings;
	UPROPERTY() TMap<FString, FString> ExpectedEnumSettings;
	UPROPERTY() TMap<FString, FWorldSettingsColorBytes> ColorSettings;
	UPROPERTY() TMap<FString, FWorldSettingsColorBytes> ExpectedColorSettings;
	UPROPERTY() TMap<FString, double> NumericSettings;
	UPROPERTY() TMap<FString, bool> BoolSettings;
	UPROPERTY() TMap<FString, FString> ObjectSettings;
	UPROPERTY() TMap<FString, FString> ExpectedObjectSettings;
	UPROPERTY() TMap<FString, FString> ClassSettings;
	UPROPERTY() TMap<FString, FString> EnumSettings;
	UPROPERTY() bool bSetNavigation = false;
	UPROPERTY() FWorldNavigationSettings Navigation;
	/** Required when replacing a stored navigation config or disabling navigation. */
	UPROPERTY() bool bConfirm = false;
	UPROPERTY() bool bDryRun = false;
	UPROPERTY() bool bSave = false;
};
