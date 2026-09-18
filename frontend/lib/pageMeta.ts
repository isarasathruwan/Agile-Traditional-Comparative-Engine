export const PRODUCT_NAME = "MethodAlign IS";

export const PUBLIC_PAGE_TITLES = {
  landing: `${PRODUCT_NAME} | Assessment`,
  progress: `${PRODUCT_NAME} | Assessment in Progress`,
  result: `${PRODUCT_NAME} | Assessment Outcome`,
};

export const ADMIN_SECTION_LABELS = {
  overview: "Overview",
  assessments: "Assessments",
  rules: "Rules",
  questionnaire: "Questionnaire",
  users: "Users",
} as const;

export type AdminSectionKey = keyof typeof ADMIN_SECTION_LABELS;

export const adminPageTitle = (section: AdminSectionKey) =>
  `${PRODUCT_NAME} | Admin - ${ADMIN_SECTION_LABELS[section]}`;
