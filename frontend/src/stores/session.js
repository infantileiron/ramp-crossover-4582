import { api, readToken, setToken } from '../api/client.js';

export const session = {
  user: null,
  async restore() {
    if (readToken()) this.user = await api.me();
  },
  async login(values) {
    const { token, user } = await api.login(values);
    setToken(token);
    this.user = user;
  },
  clear() {
    setToken(null);
    this.user = null;
  },
};
