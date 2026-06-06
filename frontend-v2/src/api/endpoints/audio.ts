import client from '../client'
import type { ASRRequest, ASRResponse, TTSRequest, TTSResponse } from '../types'

export const audioAPI = {
  asr: (data: ASRRequest) =>
    client.post<unknown, ASRResponse>('/audio/asr', data),

  tts: (data: TTSRequest) =>
    client.post<unknown, TTSResponse>('/audio/tts', data),
}
