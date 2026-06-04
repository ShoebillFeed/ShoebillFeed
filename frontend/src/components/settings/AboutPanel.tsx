import { useTranslation } from "react-i18next";

export default function AboutPanel() {
  const { t } = useTranslation();

  const steps: { title: string; desc: string }[] = [
    { title: t("about.step1"), desc: t("about.step1Desc") },
    { title: t("about.step2"), desc: t("about.step2Desc") },
    { title: t("about.step3"), desc: t("about.step3Desc") },
    { title: t("about.step4"), desc: t("about.step4Desc") },
    { title: t("about.step5"), desc: t("about.step5Desc") },
  ];

  return (
    <div>
      <h2 className="font-semibold text-gray-900 dark:text-gray-100 mb-6">{t("about.title")}</h2>

      <section className="mb-8">
        <h3 className="font-medium text-sm text-gray-900 dark:text-gray-100 mb-2">{t("about.whatTitle")}</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{t("about.whatBody")}</p>
      </section>

      <section>
        <h3 className="font-medium text-sm text-gray-900 dark:text-gray-100 mb-4">{t("about.howTitle")}</h3>
        <div className="flex flex-col gap-5">
          {steps.map(({ title, desc }, i) => (
            <div key={i} className="flex gap-4">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center text-xs font-semibold text-indigo-600 dark:text-indigo-400 mt-0.5">
                {i + 1}
              </div>
              <div>
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200">{title}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 leading-relaxed">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
