import React from 'react'
import { Link } from 'react-router-dom'
import { useTaskStore } from '../stores/taskStore'
import { usePlanStore } from '../stores/planStore'
import { TaskCard } from '../components/tasks/TaskCard'

export function DashboardPage() {
  const { tasks, fetchTasks } = useTaskStore()
  const { plans, fetchPlans } = usePlanStore()

  React.useEffect(() => {
    fetchTasks()
    fetchPlans()
  }, [])

  const today = new Date().toISOString().split('T')[0]
  const todayPlan = plans.find((p) => p.plan_date === today)

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">Dashboard</h1>
        <div className="flex space-x-4">
          <Link
            to={`/planning/${today}`}
            className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
          >
            {todayPlan ? 'Edit Plan' : 'Create Plan'}
          </Link>
          <Link
            to="/planning"
            className="inline-flex items-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
          >
            View Plans
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Your Tasks</h2>
          <div className="mt-4 space-y-4">
            {tasks.length === 0 ? (
              <p className="text-gray-500">No tasks yet. Create one!</p>
            ) : (
              tasks.slice(0, 5).map((task) => (
                <TaskCard key={task.id} task={task} />
              ))
            )}
          </div>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-gray-900">Today's Plan</h2>
          {todayPlan ? (
            <div className="mt-4 rounded-lg border border-gray-200 bg-white p-4">
              <p className="text-gray-600">{todayPlan.notes || 'No notes yet.'}</p>
              <p className="mt-2 text-sm text-gray-500">
                {todayPlan.task_order.length} tasks scheduled
              </p>
            </div>
          ) : (
            <div className="mt-4 rounded-lg border border-dashed border-gray-300 p-4">
              <p className="text-gray-500">Plan your day ahead!</p>
              <Link
                to={`/planning/${today}`}
                className="mt-2 inline-block text-indigo-600 hover:text-indigo-500"
              >
                Create your plan &rarr;
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}