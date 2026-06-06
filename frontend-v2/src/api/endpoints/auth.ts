import client from '../client'
import type { RegisterRequest, RegisterResponse } from '../types'

export const authAPI = {
  register: (data: RegisterRequest) =>
    client.post<unknown, RegisterResponse>('/auth/register', data),
}
