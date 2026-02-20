import React from 'react'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { useTaskStore } from '../../stores/taskStore'
import { TaskCard } from './TaskCard'
import { PencilIcon, TrashIcon } from '@heroicons/react/24/outline'

export function TaskList({ taskId }: { taskId: string }) {
  const { tasks, updateTask, deleteTask } = useTaskStore()
  const task = tasks.find((t) => t.id === taskId)

  if (!task) return null

  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: taskId })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  const handleComplete = async () => {
    await useTaskStore.getState().completeTask(taskId)
  }

  const handleDelete = async () => {
    await useTaskStore.getState().deleteTask(taskId)
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="mb-3 rounded-lg border border-gray-200 bg-white p-3 shadow-sm"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3 cursor-grab active:cursor-grabbing">
          <div {...attributes} {...listeners} className="text-gray-400">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
              <path d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" />
            </svg>
          </div>
          <TaskCard task={task} />
        </div>
        <div className="flex space-x-2">
          <button
            onClick={handleComplete}
            className="rounded-md bg-green-100 p-1.5 text-green-600 hover:bg-green-200"
            title="Complete task"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
          </button>
          <button
            onClick={handleDelete}
            className="rounded-md bg-red-100 p-1.5 text-red-600 hover:bg-red-200"
            title="Delete task"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}