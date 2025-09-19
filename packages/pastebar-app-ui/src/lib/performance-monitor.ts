/**
 * Performance monitoring utilities for PasteBar
 * Helps track and optimize window opening times and rendering performance
 */

interface PerformanceMetric {
  name: string
  startTime: number
  endTime?: number
  duration?: number
  metadata?: Record<string, any>
}

class PerformanceMonitor {
  private metrics: Map<string, PerformanceMetric> = new Map()
  private isEnabled: boolean = process.env.NODE_ENV === 'development'

  /**
   * Start timing a performance metric
   */
  start(name: string, metadata?: Record<string, any>): void {
    if (!this.isEnabled) return

    this.metrics.set(name, {
      name,
      startTime: performance.now(),
      metadata,
    })
  }

  /**
   * End timing a performance metric
   */
  end(name: string): number | null {
    if (!this.isEnabled) return null

    const metric = this.metrics.get(name)
    if (!metric) {
      console.warn(`Performance metric "${name}" was not started`)
      return null
    }

    const endTime = performance.now()
    const duration = endTime - metric.startTime

    metric.endTime = endTime
    metric.duration = duration

    console.log(`⚡ Performance: ${name} took ${duration.toFixed(2)}ms`, metric.metadata)

    return duration
  }

  /**
   * Measure the time it takes for a function to execute
   */
  async measure<T>(name: string, fn: () => Promise<T>, metadata?: Record<string, any>): Promise<T> {
    this.start(name, metadata)
    try {
      const result = await fn()
      this.end(name)
      return result
    } catch (error) {
      this.end(name)
      throw error
    }
  }

  /**
   * Measure synchronous function execution
   */
  measureSync<T>(name: string, fn: () => T, metadata?: Record<string, any>): T {
    this.start(name, metadata)
    try {
      const result = fn()
      this.end(name)
      return result
    } catch (error) {
      this.end(name)
      throw error
    }
  }

  /**
   * Get all recorded metrics
   */
  getMetrics(): PerformanceMetric[] {
    return Array.from(this.metrics.values()).filter(m => m.duration !== undefined)
  }

  /**
   * Clear all metrics
   */
  clear(): void {
    this.metrics.clear()
  }

  /**
   * Get average duration for a specific metric name
   */
  getAverageDuration(name: string): number | null {
    const metrics = this.getMetrics().filter(m => m.name === name)
    if (metrics.length === 0) return null

    const total = metrics.reduce((sum, m) => sum + (m.duration || 0), 0)
    return total / metrics.length
  }

  /**
   * Enable or disable performance monitoring
   */
  setEnabled(enabled: boolean): void {
    this.isEnabled = enabled
  }
}

// Global performance monitor instance
export const performanceMonitor = new PerformanceMonitor()

/**
 * React hook for measuring component render times
 */
export function usePerformanceMonitor(componentName: string) {
  const startRender = () => {
    performanceMonitor.start(`${componentName}-render`)
  }

  const endRender = () => {
    performanceMonitor.end(`${componentName}-render`)
  }

  return { startRender, endRender }
}

/**
 * Decorator for measuring function execution time
 */
export function measurePerformance(name?: string) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value
    const metricName = name || `${target.constructor.name}.${propertyKey}`

    descriptor.value = async function (...args: any[]) {
      return performanceMonitor.measure(metricName, () => originalMethod.apply(this, args))
    }

    return descriptor
  }
}

/**
 * Utility to measure window opening performance
 */
export class WindowPerformanceTracker {
  private static instance: WindowPerformanceTracker
  private windowMetrics: Map<string, { openStart: number; showStart?: number }> = new Map()

  static getInstance(): WindowPerformanceTracker {
    if (!WindowPerformanceTracker.instance) {
      WindowPerformanceTracker.instance = new WindowPerformanceTracker()
    }
    return WindowPerformanceTracker.instance
  }

  /**
   * Track when window opening process starts
   */
  trackWindowOpenStart(windowName: string): void {
    this.windowMetrics.set(windowName, {
      openStart: performance.now(),
    })
    performanceMonitor.start(`window-${windowName}-total-open`)
  }

  /**
   * Track when window becomes visible
   */
  trackWindowShow(windowName: string): void {
    const metric = this.windowMetrics.get(windowName)
    if (metric) {
      metric.showStart = performance.now()
      const creationTime = metric.showStart - metric.openStart
      console.log(`🪟 Window ${windowName} creation took ${creationTime.toFixed(2)}ms`)
    }
    performanceMonitor.start(`window-${windowName}-render`)
  }

  /**
   * Track when window is fully loaded and interactive
   */
  trackWindowReady(windowName: string): void {
    const metric = this.windowMetrics.get(windowName)
    if (metric && metric.showStart) {
      const renderTime = performance.now() - metric.showStart
      console.log(`🎨 Window ${windowName} render took ${renderTime.toFixed(2)}ms`)
    }
    
    performanceMonitor.end(`window-${windowName}-render`)
    performanceMonitor.end(`window-${windowName}-total-open`)
    
    // Clean up
    this.windowMetrics.delete(windowName)
  }
}

/**
 * Quick utility functions for common performance measurements
 */
export const perf = {
  /**
   * Measure quickpaste window opening
   */
  trackQuickPasteOpen: () => {
    WindowPerformanceTracker.getInstance().trackWindowOpenStart('quickpaste')
  },

  trackQuickPasteShow: () => {
    WindowPerformanceTracker.getInstance().trackWindowShow('quickpaste')
  },

  trackQuickPasteReady: () => {
    WindowPerformanceTracker.getInstance().trackWindowReady('quickpaste')
  },

  /**
   * Measure data loading performance
   */
  trackDataLoad: (operation: string) => ({
    start: () => performanceMonitor.start(`data-${operation}`),
    end: () => performanceMonitor.end(`data-${operation}`),
  }),

  /**
   * Measure component render performance
   */
  trackRender: (componentName: string) => ({
    start: () => performanceMonitor.start(`render-${componentName}`),
    end: () => performanceMonitor.end(`render-${componentName}`),
  }),
}
