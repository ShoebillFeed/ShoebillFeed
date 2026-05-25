export default function NewsCardSkeleton() {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-4 animate-pulse">
      <div className="flex gap-2 mb-2">
        <div className="h-5 w-20 bg-gray-200 dark:bg-gray-700 rounded" />
        <div className="h-5 w-16 bg-gray-200 dark:bg-gray-700 rounded" />
      </div>
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2" />
      <div className="h-3 bg-gray-100 dark:bg-gray-800 rounded w-full mb-1" />
      <div className="h-3 bg-gray-100 dark:bg-gray-800 rounded w-5/6" />
      <div className="mt-3 flex gap-2">
        <div className="h-7 w-7 bg-gray-100 dark:bg-gray-800 rounded" />
        <div className="h-7 w-7 bg-gray-100 dark:bg-gray-800 rounded" />
        <div className="h-7 w-7 bg-gray-100 dark:bg-gray-800 rounded" />
      </div>
    </div>
  );
}
