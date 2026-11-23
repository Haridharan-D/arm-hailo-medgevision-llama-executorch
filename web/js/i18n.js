// Add dictionaries here; translations must preserve detector decision identifiers.
export const dictionaries={en:{inspect:'Inspection station',history:'Inspection history',dashboard:'Batch overview',sop:'SOP library',audit:'Evidence & audit',settings:'Station settings',health:'System health',safety:'Advisory only. Final disposition by authorized QA personnel.'}};
export const t=(key,locale='en')=>(dictionaries[locale]||dictionaries.en)[key]||key;
