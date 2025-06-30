// API utility functions for communicating with the backend

const API_BASE_URL = '/api';

class ApiClient {
  constructor() {
    this.token = localStorage.getItem('access_token');
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('access_token');
    }
  }

  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      headers: this.getHeaders(),
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Request failed');
      }

      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Authentication methods
  async login(email, password) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    if (response.access_token) {
      this.setToken(response.access_token);
    }

    return response;
  }

  async register(userData) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await this.request('/auth/refresh', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${refreshToken}`,
      },
    });

    if (response.access_token) {
      this.setToken(response.access_token);
    }

    return response;
  }

  logout() {
    this.setToken(null);
    localStorage.removeItem('refresh_token');
  }

  // User methods
  async getProfile() {
    return this.request('/users/profile');
  }

  async updateProfile(userData) {
    return this.request('/users/profile', {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  }

  async getUsers(page = 1, perPage = 10) {
    return this.request(`/users?page=${page}&per_page=${perPage}`);
  }

  // Client methods
  async createClient(clientData) {
    return this.request('/clients', {
      method: 'POST',
      body: JSON.stringify(clientData),
    });
  }

  async getClients(page = 1, perPage = 10) {
    return this.request(`/clients?page=${page}&per_page=${perPage}`);
  }

  // Document methods
  async createDocument(documentData) {
    return this.request('/documents', {
      method: 'POST',
      body: JSON.stringify(documentData),
    });
  }

  async getDocuments(page = 1, perPage = 10, status = null) {
    let url = `/documents?page=${page}&per_page=${perPage}`;
    if (status) {
      url += `&status=${status}`;
    }
    return this.request(url);
  }

  async getDocument(documentId) {
    return this.request(`/documents/${documentId}`);
  }

  async updateDocument(documentId, documentData) {
    return this.request(`/documents/${documentId}`, {
      method: 'PUT',
      body: JSON.stringify(documentData),
    });
  }

  async addDocumentField(documentId, fieldData) {
    return this.request(`/documents/${documentId}/fields`, {
      method: 'POST',
      body: JSON.stringify(fieldData),
    });
  }

  async updateDocumentField(documentId, fieldId, fieldData) {
    return this.request(`/documents/${documentId}/fields/${fieldId}`, {
      method: 'PUT',
      body: JSON.stringify(fieldData),
    });
  }

  // Template methods
  async uploadTemplate(formData) {
    return this.request('/documents/templates', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
      },
      body: formData,
    });
  }

  async getTemplates(page = 1, perPage = 10) {
    return this.request(`/documents/templates?page=${page}&per_page=${perPage}`);
  }
}

export const apiClient = new ApiClient();

