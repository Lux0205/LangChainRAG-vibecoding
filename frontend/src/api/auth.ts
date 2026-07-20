import request from './request'

export function register(username: string, password: string) {
  return request.post('/auth/register', { username, password })
}

export function login(username: string, password: string) {
  return request.post('/auth/login', { username, password })
}

export function getMe() {
  return request.get('/auth/me')
}

export function changePassword(oldPassword: string, newPassword: string) {
  return request.put('/auth/password', {
    old_password: oldPassword,
    new_password: newPassword,
  })
}
