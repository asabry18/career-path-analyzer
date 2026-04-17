interface PageHeaderProps {
  title: string;
  subtitle: string;
}

export default function PageHeader({ title, subtitle }: PageHeaderProps) {
  return (
    <>
      <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
        {title}
      </h1>
      <p className="text-gray-500 dark:text-gray-400 mt-2 mb-8">{subtitle}</p>
    </>
  );
}
