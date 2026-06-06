import client from '../client'
import type {
  PublicQuestionRequest, PublicQuestionResponse,
  VoiceQuestionRequest, VoiceQuestionResponse,
} from '../types'

export const aiAPI = {
  publicQuestion: (data: PublicQuestionRequest) =>
    client.post<unknown, PublicQuestionResponse>('/ai/public-question', data),

  voiceQuestion: (data: VoiceQuestionRequest) =>
    client.post<unknown, VoiceQuestionResponse>('/ai/public-voice-question', data),
}
