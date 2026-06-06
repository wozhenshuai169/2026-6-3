import client from '../client'
import type {
  CreateRoomRequest, CreateRoomResponse,
  JoinRoomRequest, JoinRoomResponse,
  RoomStatusResponse,
  UpdateSpotRequest, UpdateSpotResponse,
  AvatarStateResponse,
} from '../types'

export const roomsAPI = {
  create: (data: CreateRoomRequest) =>
    client.post<unknown, CreateRoomResponse>('/rooms', data),

  getStatus: (roomId: string) =>
    client.get<unknown, RoomStatusResponse>(`/rooms/${roomId}`),

  join: (roomId: string, data: JoinRoomRequest) =>
    client.post<unknown, JoinRoomResponse>(`/rooms/${roomId}/join`, data),

  updateSpot: (roomId: string, data: UpdateSpotRequest) =>
    client.post<unknown, UpdateSpotResponse>(`/rooms/${roomId}/current-spot`, data),

  getAvatarState: (roomId: string) =>
    client.get<unknown, AvatarStateResponse>(`/rooms/${roomId}/avatar-state`),
}
