import client from '../client'
import type { VisionRecognizeRequest, VisionRecognizeResponse } from '../types'

export const visionAPI = {
  recognize: (data: VisionRecognizeRequest) =>
    client.post<unknown, VisionRecognizeResponse>('/vision/recognize', data),
}
