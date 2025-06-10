import React, { useState, useEffect, useRef } from "react";
import { useMeeting } from "@videosdk.live/react-sdk";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AgentSettings, PROMPTS } from "./types";
import { AgentAudioPlayer } from "./AgentAudioPlayer";
import { VITE_VIDEOSDK_TOKEN, VITE_API_URL } from "./types";
import MicWithSlash from "../icons/MicWithSlash";
import { WaveAvatar } from "./WaveAvatar";
import { RoomLayout } from "../layout/RoomLayout";

interface MeetingInterfaceProps {
  meetingId: string;
  onDisconnect: () => void;
  agentSettings: AgentSettings;
  onSettingsChange?: (settings: AgentSettings) => void;
}

export const MeetingInterface: React.FC<MeetingInterfaceProps> = ({
  meetingId,
  onDisconnect,
  agentSettings,
  onSettingsChange,
}) => {
  const [agentInvited, setAgentInvited] = useState(false);
  const [micEnabled, setMicEnabled] = useState(true);
  const [isJoined, setIsJoined] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [retryAttempts, setRetryAttempts] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);
  const joinAttempted = useRef(false);
  const agentInviteAttempted = useRef(false);
  const maxRetries = 3;
  const retryDelay = 5000;

  const { join, leave, end, toggleMic, participants, localParticipant } =
    useMeeting({
      onMeetingJoined: () => {
        console.log("Meeting joined successfully");
        setIsJoined(true);
        setConnectionError(null);
        setRetryAttempts(0);
        setIsRetrying(false);
        joinAttempted.current = true;
      },
      onMeetingLeft: () => {
        console.log("Meeting left");
        setIsJoined(false);
        setRetryAttempts(0);
        setIsRetrying(false);
        joinAttempted.current = false;
        agentInviteAttempted.current = false;
        onDisconnect();
      },
      onParticipantJoined: (participant) => {
        console.log("Participant joined:", participant.displayName);
      },
      onParticipantLeft: (participant) => {
        console.log("Participant left:", participant.displayName);
      },
      onSpeakerChanged: (activeSpeakerId) => {
        console.log("Speaker changed:", activeSpeakerId);
      },
      onError: (error) => {
        console.error("Meeting error:", error);

        if (error.message?.includes("Insufficient resources")) {
          setConnectionError(
            "Server is currently overloaded. Please try again in a few minutes."
          );

          if (retryAttempts < maxRetries && !isRetrying) {
            setIsRetrying(true);
            setTimeout(() => {
              handleRetryConnection();
            }, retryDelay);
          } else {
            console.error("Max retry attempts reached");
          }
        } else {
          setConnectionError(error.message || "Connection failed");
          console.error("Meeting error:", error);
        }
      },
    });

  useEffect(() => {
    if (isJoined && !agentInvited && !agentInviteAttempted.current) {
      console.log("Auto-inviting agent after meeting join");
      agentInviteAttempted.current = true;
      inviteAgent();
    }
  }, [isJoined]);

  const handleRetryConnection = () => {
    if (retryAttempts >= maxRetries) {
      setIsRetrying(false);
      setConnectionError(
        "Maximum retry attempts reached. Please try creating a new meeting."
      );
      return;
    }

    console.log(`Retry attempt ${retryAttempts + 1}/${maxRetries}`);
    setRetryAttempts((prev) => prev + 1);

    try {
      setConnectionError(null);
      joinAttempted.current = false;

      setTimeout(() => {
        if (!isJoined && !joinAttempted.current) {
          join();
          joinAttempted.current = true;
        }
        setIsRetrying(false);
      }, 1000);
    } catch (error) {
      console.error("Error during retry:", error);
      setIsRetrying(false);
    }
  };

  useEffect(() => {
    if (!joinAttempted.current && !isRetrying) {
      console.log("Attempting to join meeting:", meetingId);

      const timer = setTimeout(() => {
        if (!isJoined && !joinAttempted.current) {
          try {
            join();
            joinAttempted.current = true;
          } catch (error) {
            console.error("Error joining meeting:", error);
            setConnectionError("Failed to join meeting");
          }
        }
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [join, meetingId, isRetrying]);

  const handleToggleMic = () => {
    if (isJoined) {
      toggleMic();
      setMicEnabled(!micEnabled);
    } else {
      console.log("Not Connected : Please connect to the meeting first");
    }
  };

  const leaveAgent = async () => {
    try {
      const response = await fetch(`${VITE_API_URL}/leave-agent`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          meeting_id: meetingId,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Agent leave response:", data);

        if (data.status === "removed") {
          console.log("Agent successfully removed, ending meeting");
          end(); // Call the end method from useMeeting hook
          console.log("AI agent removed from meeting");
        } else if (data.status === "not_found") {
          console.log("No agent session found");
          console.log("No AI agent session found, leaving meeting normally");
        }
      } else {
        const errorData = await response.json();
        console.error("Error removing agent:", errorData);
        console.warn("Could not remove AI agent from meeting");
      }
    } catch (error) {
      console.error("Error calling leave-agent API:", error);
      console.warn("Could not remove AI agent from meeting");
    }
  };

  const handleDisconnect = async () => {
    try {
      if (agentInvited) {
        await leaveAgent();
      } else {
        // If no agent is invited, just leave the meeting normally
        leave();
      }
    } catch (error) {
      console.error("Error during disconnect:", error);
      leave();
    }
  };

  const handleManualRetry = () => {
    if (isRetrying) return;

    setRetryAttempts(0);
    setConnectionError(null);
    joinAttempted.current = false;
    handleRetryConnection();
  };

  const inviteAgent = async () => {
    try {
      console.log("Sending agent settings:", agentSettings);

      // Determine which prompt to use
      let systemPrompt: string;

      if (agentSettings.personality === "Custom") {
        // Use custom prompt if Custom personality is selected
        systemPrompt = agentSettings.customPrompt || "";
      } else {
        // Use predefined prompt for the selected personality
        systemPrompt =
          PROMPTS[agentSettings.personality as keyof typeof PROMPTS];
      }

      const response = await fetch(`${VITE_API_URL}/join-agent`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          meeting_id: meetingId,
          token: VITE_VIDEOSDK_TOKEN,
          model: agentSettings.model,
          voice: agentSettings.voice,
          personality: agentSettings.personality,
          system_prompt: systemPrompt, // Use the determined prompt
          temperature: agentSettings.temperature,
          topP: agentSettings.topP,
          topK: Math.round(agentSettings.topK),
        }),
      });

      if (response.ok) {
        setAgentInvited(true);
        console.log("Agent invited successfully");
      } else {
        throw new Error("Failed to invite agent");
      }
    } catch (error) {
      console.error("Error inviting agent:", error);
      agentInviteAttempted.current = false;
      console.warn("Could not invite AI agent to meeting");
    }
  };

  const participantsList = Array.from(participants.values());
  const agentParticipant = participantsList.find(
    (p) => p.displayName?.includes("Agent") || p.displayName?.includes("Haley")
  );

  return (
    <RoomLayout
      agentSettings={agentSettings}
      onSettingsChange={onSettingsChange}
    >
      <div className="flex flex-col items-center justify-between min-h-[400px] w-[300px] h-[50%]">
        {/* Agent Avatar with Wave Animation */}
        <WaveAvatar
          participantId={agentParticipant?.id}
          isConnected={isJoined}
          className="mb-8"
        />

        {/* Control Panel */}
        <div className="flex items-center space-x-6">
          {/* Microphone Control */}
          <Button
            onClick={handleToggleMic}
            size="lg"
            className="w-12 h-8  bg-[#1F1F1F] hover:bg-[#1F1F1F]"
            disabled={!isJoined}
          >
            <MicWithSlash disabled={!micEnabled} />
          </Button>

          {/* Disconnect Button */}
          <Button
            onClick={handleDisconnect}
            variant="destructive"
            className="px-6 py-3 bg-[#380b0b] hover:bg-[#380b0b] text-[#a13f3f]"
          >
            Disconnect
          </Button>

          {/* Retry Button */}
          {connectionError && !isRetrying && retryAttempts < maxRetries && (
            <Button
              onClick={handleManualRetry}
              variant="outline"
              className="px-6 py-3"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          )}
        </div>
      </div>

      {/* Agent Audio Player */}
      {agentParticipant && (
        <div>
          <AgentAudioPlayer participantId={agentParticipant.id} />
        </div>
      )}
    </RoomLayout>
  );
};
