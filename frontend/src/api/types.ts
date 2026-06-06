// ============ Auth ============

export interface RegisterRequest {
  userName: string;
  password: string;
}

export interface RegisterResponse {
  userId: string;
  userName: string;
  token: string;
}

// ============ Room ============

export interface CreateRoomRequest {
  token: string;
  roomName: string;
  scenicAreaId: string;
  routeId: string;
}

export interface CreateRoomResponse {
  roomId: string;
  status: string;
}

export interface JoinRoomRequest {
  token: string;
}

export interface JoinRoomResponse {
  roomId: string;
  userId: string;
  status: string;
}

export interface RoomState {
  roomId: string;
  members: { userId: string; userName: string }[];
  currentSpot: string;
  status: string;
}

export interface UpdateSpotRequest {
  spotId: string;
}

export interface UpdateSpotResponse {
  roomId: string;
  currentSpot: string;
  status: string;
}

// ============ Digital Human (Avatar State) ============

export type AIStatus =
  | 'idle'
  | 'listening'
  | 'speaking'
  | 'thinking'
  | 'paused'
  | 'resuming';

export type Emotion = 'friendly' | 'neutral' | 'thinking' | 'surprised';

export interface AvatarState {
  aiStatus: AIStatus;
  emotion: Emotion;
  action: string;
  text: string;
  audioUrl: string;
}

// ============ AI Q&A ============

export interface PublicQuestionRequest {
  roomId: string;
  userId: string;
  question: string;
}

export interface PublicQuestionResponse {
  roomId: string;
  answer: string;
}

export interface VoiceQuestionRequest {
  roomId: string;
  userId: string;
  channel: 'public' | 'private';
  audioUrl: string;
}

export interface VoiceQuestionResponse {
  asrText: string;
  decision: string;
  answer: string;
  audioUrl: string;
  resumeText: string;
  resumeAudioUrl: string;
  sources: KnowledgeSource[];
}

export interface KnowledgeSource {
  title: string;
  chunkId: string;
}

// ============ ASR / TTS ============

export interface ASRRequest {
  roomId: string;
  userId: string;
  channel: 'public' | 'private';
  audioUrl: string;
  audioFormat?: 'wav' | 'mp3';
}

export interface ASRResponse {
  text: string;
  confidence: number;
  language?: string;
  format?: string;
}

export interface TTSRequest {
  text: string;
  voice?: string;
  speed?: number;
}

export interface TTSResponse {
  audioUrl: string;
  durationMs: number;
  voice?: string;
  format?: string;
}

// ============ Vision ============

export interface VisionRequest {
  roomId: string;
  userId: string;
  imageUrl: string;
  currentSpotId?: string;
}

export interface VisionResponse {
  recognizedSpot: {
    spotId: string;
    spotName: string;
    confidence: number;
  };
  description: string;
  visualFeatures?: string[];
  relatedSpots: { spotId: string; spotName: string }[];
}

// ============ Route Recommendation ============

export interface RouteRecommendRequest {
  roomId: string;
  userId: string;
  preferences: {
    interest: string[];
    timeLimit: number;
    physicalStrength: 'low' | 'medium' | 'high';
    withChildren: boolean;
    withElderly: boolean;
    avoidCrowd: boolean;
  };
}

export interface RouteRecommendResponse {
  routeName: string;
  estimatedTime: number;
  spots: { spotId: string; spotName: string; stayMinutes: number }[];
  reason: string;
  difficulty?: 'low' | 'medium' | 'high';
  walkingDifficulty?: 'low' | 'medium' | 'high';
  suitableForChildren?: boolean;
  suitableForElderly?: boolean;
  distance?: number;
  matchedPreferences?: string[];
  scoreBreakdown?: Record<string, number>;
}

// ============ Chat Messages (frontend-only) ============

export type Channel = 'public' | 'private';

export interface ChatMessage {
  msgId: string;
  roomId: string;
  userId: string;
  nickname: string;
  channel: Channel;
  role: 'user' | 'ai' | 'system';
  text: string;
  sources?: KnowledgeSource[];
  createdAt: string;
}

// ============ Knowledge ============

export interface KnowledgeDoc {
  docId: string;
  fileName: string;
  fileType: string;
  scenicAreaId: string;
  uploadAt: string;
  status: 'processing' | 'ready' | 'error';
}

// ============ Dashboard ============

export interface DashboardSummary {
  todayQuestions: number;
  publicQuestions: number;
  privateQuestions: number;
  knowledgeHitRate: number;
  topQuestions: { question: string; count: number }[];
  onlineRooms: number;
  onlineUsers: number;
  avgSatisfaction: number;
}

export interface ChatLog {
  logId: string;
  roomId: string;
  userId: string;
  channel: Channel;
  question: string;
  answer: string;
  intent: string;
  decision: string;
  knowledgeHit: boolean;
  createdAt: string;
}

// ============ Leader Private Requests ============

export interface PrivateRequest {
  id: string;
  roomId: string;
  userId: string;
  nickname: string;
  content: string;
  aiReply: string;
  needLeaderConfirm: boolean;
  status: 'pending' | 'notified' | 'resolved';
  createdAt: string;
}

// ============ Tour State (for leader control) ============

export interface TourState {
  roomId: string;
  currentSpotId: string;
  currentSpotName: string;
  currentScriptSegment: string;
  resumePoint: string;
  aiStatus: string;
  tourStage: string;
  nextSpotId: string;
  onlineUsers: number;
  pendingPrivateRequests: number;
}
