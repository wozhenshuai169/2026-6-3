import client from '../client'
import type { RouteRecommendRequest, RouteRecommendResponse } from '../types'

export const recommendAPI = {
  getRoute: (data: RouteRecommendRequest) =>
    client.post<unknown, RouteRecommendResponse>('/recommend/route', data),
}
