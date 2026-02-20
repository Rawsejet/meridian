import React from 'react'
import { useParams, Link } from 'react-router-dom'
import { usePlanStore } from '../stores/planStore'
import { useTaskStore } from '../stores/taskStore'
import { TaskList } from '../components/tasks/TaskList'
import { TaskFormModal } from '../components/tasks/TaskFormModal'
import { useDndContext } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'

export function PlanningPage() {
  const { date } = useParams<{ date: string }>()
  const { plan, createPlan, updatePlan, addTaskToPlan, removeTaskFromPlan, fetchPlan } = usePlanStore()
  const { tasks, fetchTasks } = useTaskStore()

  React.useEffect(() => {
    fetchTasks()
  }, [])

  React.useEffect(() => {
    if (date) {
      fetchPlan(date).catch(console.error)
    }
  }, [date, fetchPlan])

  const [showTaskModal, setShowTaskModal] = React.useState(false)

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">
          Daily Plan - {date}
        </h1>
        <div className="flex space-x-4">
          <button
            onClick={() => setShowTaskModal(true)}
            className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
          >
            Add Task
          </button>
          <Link
            to="/"
            className="inline-flex items-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
        <div className="md:col-span-2">
          <h2 className="text-xl font-semibold text-gray-900">Task Order</h2>
          <div className="mt-4 space-y-4">
            {plan?.task_order && plan.task_order.length > 0 ? (
              <SortableContext
                items={plan.task_order}
                strategy={verticalListSortingStrategy}
              >
                {plan.task_order.map((taskId) => (
                  <TaskList key={taskId} taskId={taskId} />
                ))}
              </SortableContext>
            ) : (
              <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center">
                <p className="text-gray-500">No tasks scheduled for today.</p>
                <button
                  onClick={() => setShowTaskModal(true)}
                  className="mt-2 text-indigo-600 hover:text-indigo-500"
                >
                  Add some tasks &rarr;
                </button>
              </div>
            )}
          </div>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-gray-900">Plan Details</h2>
          <div className="mt-4 rounded-lg border border-gray-200 bg-white p-4">
            <label className="block text-sm font-medium text-gray-700">Notes</label>
            <textarea
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              rows={3}
              placeholder="Add notes for today..."
            />
          </div>
        </div>
      </div>

      {showTaskModal && (
        <TaskFormModal onClose={() => setShowTaskModal(false)} />
      )}
    </div>
  )
}