import { create } from 'zustand'
import axios from 'axios'
import { useAuthStore } from './authStore'

export interface Task {
  id: string
  user_id: string
  title: string
  description?: string
  due_date?: string
  priority: number
  estimated_minutes?: number
  energy_level?: number
  category?: string
  status: string
  completed_at?: string
  created_at: string
  updated_at: string
}

interface TaskState {
  tasks: Task[]
  isLoading: boolean
  error: string | null

  fetchTasks: () => Promise<void>
  createTask: (task: Partial<Task>) => Promise<Task>
  updateTask: (id: string, task: Partial<Task>) => Promise<Task>
  deleteTask: (id: string) => Promise<void>
  completeTask: (id: string) => Promise<Task>
}

const API_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'

export const useTaskStore = create<TaskState>((set, get) => ({
  tasks: [],
  isLoading: false,
  error: null,

  fetchTasks: async () => {
    set({ isLoading: true, error: null })
    try {
      const token = useAuthStore.getState().token
      const response = await axios.get(`${API_URL}/api/v1/tasks`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      set({ tasks: response.data.tasks, isLoading: false })
    } catch (error: any) {
      set({ isLoading: false, error: error.response?.data?.detail?.message || 'Failed to fetch tasks' })
      throw error
    }
  },

  createTask: async (task: Partial<Task>) => {
    set({ isLoading: true, error: null })
    try {
      const token = useAuthStore.getState().token
      const response = await axios.post(
        `${API_URL}/api/v1/tasks`,
        task,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      )
      set((state) => ({ tasks: [response.data, ...state.tasks], isLoading: false }))
      return response.data
    } catch (error: any) {
      set({ isLoading: false, error: error.response?.data?.detail?.message || 'Failed to create task' })
      throw error
    }
  },

  updateTask: async (id: string, task: Partial<Task>) => {
    set({ isLoading: true, error: null })
    try {
      const token = useAuthStore.getState().token
      const response = await axios.patch(
        `${API_URL}/api/v1/tasks/${id}`,
        task,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      )
      set((state) => ({
        tasks: state.tasks.map((t) => (t.id === id ? response.data : t)),
        isLoading: false,
      }))
      return response.data
    } catch (error: any) {
      set({ isLoading: false, error: error.response?.data?.detail?.message || 'Failed to update task' })
      throw error
    }
  },

  deleteTask: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      const token = useAuthStore.getState().token
      await axios.delete(`${API_URL}/api/v1/tasks/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      set((state) => ({
        tasks: state.tasks.filter((t) => t.id !== id),
        isLoading: false,
      }))
    } catch (error: any) {
      set({ isLoading: false, error: error.response?.data?.detail?.message || 'Failed to delete task' })
      throw error
    }
  },

  completeTask: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      const token = useAuthStore.getState().token
      const response = await axios.post(
        `${API_URL}/api/v1/tasks/${id}/complete`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      )
      set((state) => ({
        tasks: state.tasks.map((t) => (t.id === id ? response.data : t)),
        isLoading: false,
      }))
      return response.data
    } catch (error: any) {
      set({ isLoading: false, error: error.response?.data?.detail?.message || 'Failed to complete task' })
      throw error
    }
  },
}))