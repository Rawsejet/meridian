import React from 'react'
import { Task } from '../../stores/taskStore'

const priorityColors = {
  1: 'bg-green-100 text-green-800',
  2: 'bg-blue-100 text-blue-800',
  3: 'bg-yellow-100 text-yellow-800',
  4: 'bg-red-100 text-red-800',
}

const priorityLabels = {
  1: 'Low',
  2: 'Medium',
  3: 'High',
  4: 'Urgent',
}

export function TaskCard({ task }: { task: Task }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-sm font-medium text-gray-900">{task.title}</h3>
          {task.description && (
            <p className="mt-1 text-sm text-gray-500">{task.description}</p>
          )}
          {task.category && (
            <span className="mt-2 inline-flex items-center rounded-full bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600">
              {task.category}
            </span>
          )}
        </div>
        <span
          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
            priorityColors[task.priority as keyof typeof priorityColors] || priorityColors[2]
          }`}
        >
          {priorityLabels[task.priority as keyof typeof priorityLabels]}
        </span>
      </div>
      <div className="mt-4 flex items-center space-x-4 text-xs text-gray-500">
        {task.due_date && <span>Due: {task.due_date}</span>}
        {task.estimated_minutes && <span>{task.estimated_minutes} min</span>}
      </div>
    </div>
  )
}