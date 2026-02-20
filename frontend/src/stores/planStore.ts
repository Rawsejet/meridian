import { create } from 'zustand'
import apiClient from '../lib/apiClient'
import { useAuthStore } from './authStore'

export interface Plan {
  id: string
  user_id: string
  plan_date: string
  task_order: string[]
  notes?: string
  mood?: number
  created_at: string
  updated_at: string
}

interface PlanState {
  plans: Plan[]
  plan: Plan | null
  isLoading: boolean
  error: string | null

  fetchPlans: () => Promise<void>
  fetchPlan: (date: string) => Promise<void>
  createPlan: (date: string, plan: Partial<Plan>) => Promise<Plan>
  updatePlan: (date: string, plan: Partial<Plan>) => Promise<Plan>
  reorderTasks: (date: string, taskOrder: string[]) => Promise<Plan>
  completePlan: (date: string, completions: Record<string, boolean>) => Promise<any>
  addTaskToPlan: (date: string, taskId: string) => Promise<Plan>
  removeTaskFromPlan: (date: string, taskId: string) => Promise<Plan | null>
}

const API_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'

export const usePlanStore = create<PlanState>((set, get) => ({
  plans: [],
  plan: null,
  isLoading: false,
  error: null,

  fetchPlans: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await apiClient.get(`${API_URL}/api/v1/plans?days=30`)
      set({ plans: response.data.plans, isLoading: false })
    } catch (error: any) {
      set({ isLoading: false, error: error.response?.data?.detail?.message || 'Failed to fetch plans' })
      throw error
    }
  },

  fetchPlan: async (date: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await apiClient.get(`${API_URL}/api/v1/plans/${date}`)
      set({ plan: response.data, isLoading: false })
    } catch (error: any) {
      set({ isLoading: false, error: error.response?.data?.detail?.message || 'Failed to fetch plan' })
      throw error
    }
  },

  createPlan: async (date: string, plan: Partial<Plan>) => {
    set({ isLoading: true, error: null })
    try {
      const response = await apiClient.post(`${API_URL}/api/v1/plans/${date}`, plan)
      set((state) => ({
        plans: [response.data, ...state.plans],
        plan: response.data,
        isLoading: false,
      }))
      return response.data
    } catch (error: any) {
      set({ isLoading: false, error: error.response?.data?.detail?.message || 'Failed to create plan' })
      throw error
    }
  },

  updatePlan: async (date: string, plan: Partial<Plan>) => {
    set({ isLoading: true, error: null })
    try {
      const response = await apiClient.patch(`${API_URL}/api/v1/plans/${date}`, plan)
      set((state) => ({
        plans: state.plans.map((p) => (p.plan_date === date ? response.data : p)),
        plan: response.data,
        isLoading: false,
      }))
      return response.data
    } catch (error: any) {
      set({ isLoading: false, error: error.response?.data?.detail?.message || 'Failed to update plan' })
      throw error
    }
  },

  reorderTasks: async (date: string, taskOrder: string[]) => {
    set({ isLoading: true, error: null })
    try {
      const response = await apiClient.patch(`${API_URL}/api/v1/plans/${date}/reorder`, { task_order: taskOrder })
      set((state) => ({
        plans: state.plans.map((p) => (p.plan_date === date ? response.data : p)),
        plan: response.data,
        isLoading: false,
      }))
      return response.data
    } catch (error: any) {
      set({ isLoading: false, error: error.response?.data?.detail?.message || 'Failed to reorder tasks' })
      throw error
    }
  },

  completePlan: async (date: string, completions: Record<string, boolean>) => {
    set({ isLoading: true, error: null })
    try {
      const response = await apiClient.post(`${API_URL}/api/v1/plans/${date}/complete`, { task_completions: completions })
      return response.data
    } catch (error: any) {
      set({ isLoading: false, error: error.response?.data?.detail?.message || 'Failed to complete plan' })
      throw error
    }
  },

  addTaskToPlan: async (date: string, taskId: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await apiClient.post(`${API_URL}/api/v1/plans/${date}/tasks`, { task_id: taskId })
      set((state) => ({
        plans: state.plans.map((p) => (p.plan_date === date ? response.data : p)),
        plan: response.data,
        isLoading: false,
      }))
      return response.data
    } catch (error: any) {
      set({ isLoading: false, error: error.response?.data?.detail?.message || 'Failed to add task to plan' })
      throw error
    }
  },

  removeTaskFromPlan: async (date: string, taskId: string) => {
    set({ isLoading: true, error: null })
    try {
      await apiClient.delete(`${API_URL}/api/v1/plans/${date}/tasks/${taskId}`)
      // Update the plan's task_order by removing the task
      set((state) => {
        if (!state.plan || state.plan.plan_date !== date) return state
        const updatedTaskOrder = state.plan.task_order.filter((id) => id !== taskId)
        const updatedPlan = { ...state.plan, task_order: updatedTaskOrder }
        return {
          plans: state.plans.map((p) => (p.plan_date === date ? updatedPlan : p)),
          plan: updatedPlan,
          isLoading: false,
        }
      })
      // Get the updated plan from state
      const currentPlan = get().plan
      return currentPlan || null
    } catch (error: any) {
      set({ isLoading: false, error: error.response?.data?.detail?.message || 'Failed to remove task from plan' })
      throw error
    }
  },
}))