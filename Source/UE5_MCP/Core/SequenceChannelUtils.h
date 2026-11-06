#pragma once
#include "CoreMinimal.h"
struct FRenderTargetReq;
namespace SequenceChannelUtils { FString CameraCutTrackPolicy(const FRenderTargetReq& R); FString MarkedFrames(const FRenderTargetReq& R); FString TrackMutePolicy(const FRenderTargetReq& R); FString TrackEvaluationPolicy(const FRenderTargetReq& R); FString RemoveEventEndpointPin(const FRenderTargetReq& R); FString AddEventEndpointPin(const FRenderTargetReq& R); FString EventTrackPolicy(const FRenderTargetReq& R); FString DiscoverEventEndpoints(const FRenderTargetReq& R); FString Extrapolation(const FRenderTargetReq& R); }
