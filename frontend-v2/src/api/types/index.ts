// ============ 用户 (app/schemas/users.py) ============
export interface RegisterRequest {
  userName: string
  password: string
}
export interface RegisterResponse {
  userId: string
  userName: string
  token: string
}

// ============ 房间 (app/schemas/rooms.py) ============
export interface CreateRoomRequest {
  token: string
  roomName: string
  scenicAreaId: string
  routeId: string
}
export interface CreateRoomResponse {
  roomId: string
  status: string
}
export interface JoinRoomRequest {
  token: string
}
export interface JoinRoomResponse {
  roomId: string
  userId: string
  status: string
}
export interface Member {
  userId: string
  userName: string
}
export interface RoomStatusResponse {
  roomId: string
  members: Member[]
  currentSpot: string
  status: string
}
export interface UpdateSpotRequest {
  spotId: string
}
export interface UpdateSpotResponse {
  roomId: string
  currentSpot: string
  status: string
}

// ============ 数字人状态 (app/schemas/avatar.py) ============
export type AIStatus = 'idle' | 'listening' | 'speaking' | 'thinking' | 'paused' | 'resuming'
export type Emotion = 'friendly' | 'neutral' | 'thinking' | 'surprised'
export interface AvatarStateResponse {
  aiStatus: string
  emotion: string
  action: string
  text: string
  audioUrl: string
}

// ============ AI 问答 (app/schemas/ai.py) ============
export interface PublicQuestionRequest {
  roomId: string
  userId: string
  question: string
  needAudio?: boolean
}
export interface PublicQuestionResponse {
  roomId: string
  answer: string
  audioUrl?: string | null
  duration: number
  sources: SourceSchema[]
  avatarState: PublicAvatarState
  warning?: string | null
}
export interface SourceSchema {
  title: string
  chunkId: string
}
export interface PublicAvatarState {
  status: string
  emotion: string
  action: string
  mouthOpen: boolean
}
export interface VoiceQuestionRequest {
  roomId: string
  userId: string
  channel?: string       // default "public"
  audioUrl: string
  audioFormat?: string | null   // "wav" | "mp3"
  textHint?: string | null
}
export interface VoiceQuestionResponse {
  asrText: string
  decision: string
  answer: string
  audioUrl?: string | null
  duration: number
  resumeText: string
  resumeAudioUrl?: string | null
  resumeDuration: number
  sources: SourceSchema[]
  avatarState: PublicAvatarState
  warning?: string | null
  events: Record<string, unknown>[]
}

// ============ 音频 (app/schemas/audio.py) ============
export interface ASRRequest {
  roomId: string
  userId: string
  channel: string       // "public" | "private"
  audioUrl: string
  audioFormat?: string | null
  textHint?: string | null
}
export interface ASRResponse {
  text: string
  confidence: number
}
export interface TTSRequest {
  text: string
  voice?: string         // default "guide_female"
  speed?: number         // default 1.0
  audioFormat?: string   // default "mp3"
}
export interface TTSResponse {
  audioUrl: string
  duration: number
}

// ============ 视觉识别 (app/schemas/vision.py) ============
export interface VisionRecognizeRequest {
  roomId: string
  userId: string
  imageUrl: string
  currentSpotId?: string
}
export interface RecognizedSpot {
  spotId: string
  spotName: string
  confidence: number
}
export interface RelatedSpot {
  spotId: string
  spotName: string
}
export interface VisionRecognizeResponse {
  recognizedSpot: RecognizedSpot
  description: string
  relatedSpots: RelatedSpot[]
  visualFeatures: string[]
  category: string       // "spot" | "person" | "object" | "scene" | "unknown"
}

// ============ 路线推荐 (app/schemas/recommend.py) ============
export interface RoutePreferences {
  interest: string[]
  timeLimit: number
  physicalStrength: 'low' | 'medium' | 'high'
  withChildren: boolean
  withElderly: boolean
  avoidCrowd: boolean
}
export interface RouteRecommendRequest {
  roomId: string
  userId: string
  preferences: RoutePreferences
}
export interface RouteSpot {
  spotId: string
  spotName: string
  stayMinutes: number
}
export interface RouteRecommendResponse {
  routeId: string
  routeName: string
  score: number
  estimatedTime: number
  spots: RouteSpot[]
  reason: string
  distance: number
  difficulty: string       // "" | "low" | "medium" | "high"
  matchedPreferences: string[]
  scoreBreakdown: Record<string, number>
}

// ============ 前端内部类型（非后端接口） ============
export interface RoomMessage {
  id: string
  userId: string
  userName: string
  content: string
  type: 'user' | 'ai' | 'system'
  timestamp: number
  audioUrl?: string
}

export interface PrivateMessage {
  id: string
  fromUserId: string
  fromUserName: string
  toUserId: string
  content: string
  timestamp: number
}

// 团长角色通过房间创建者推断（后端 Member 无 role 字段）
export interface MemberWithRole extends Member {
  role: 'leader' | 'visitor'
}
