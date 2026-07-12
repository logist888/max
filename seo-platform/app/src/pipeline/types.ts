// Типы снимка «ВУЗ-навигатора» (вход) и нормализованной модели (выход).
// Правила: пропуск данных = null, никогда не 0 и не выдуманное значение.

export interface RawProgram {
  okso: string;
  name: string;
  level: string;
  form: string;
  placeType: string;
  places: number;
  cost: number;
}

export interface RawOrg {
  id: string;
  name: string;
  fullName: string;
  shortName: string;
  region: string;
  city: string;
  address?: string;
  url: string;
  phones?: string[];
  emails?: string[];
  websites?: string[];
  indicators?: Record<string, string>;
  militaryDept: boolean;
  dormitory: boolean;
  usefulLinks?: Record<string, string>;
  socials?: Record<string, string>;
  programs?: RawProgram[];
  parsedAt?: string;
}

export type OrgKind = 'головной' | 'филиал' | 'зарубежный';

export interface Offer {
  okso: string;
  level: string;
  form: string;
  placeType: string;
  places: number | null;
  cost: number | null; // null = «Информация отсутствует» (в т.ч. после санитарии)
}

export interface Org {
  id: string;
  slug: string;
  kind: OrgKind;
  shortName: string;
  name: string;
  fullName: string;
  regionKey: string;
  cityKey: string; // ключ сущности «город»: region + нормализованное имя
  address: string | null;
  phones: string[];
  emails: string[];
  websites: string[];
  militaryDept: boolean;
  dormitory: boolean;
  dormPlaces: number | null;
  usefulLinks: Record<string, string>;
  vk: string | null;
  acronyms: string[];
  offers: Offer[];
  levelsDeclared: string[]; // индикатор источника (включая невыгружаемые уровни)
  levelsNotExported: string[]; // заявлены, но программ нет (ординатура и т.п.)
}

export interface City {
  key: string;
  slug: string;
  displayName: string;
  regionKey: string;
  rawNames: string[];
}

export interface Region {
  key: string;
  slug: string;
  displayName: string;
}

export interface Direction {
  okso: string;
  slug: string;
  name: string;
  level: string;
  ugsCode: string; // '' у научных специальностей аспирантуры/ординатуры
  scientific: boolean; // код номенклатуры научных специальностей (формат 5.1.4), не ФГОС
}

export interface SanitationEntry {
  orgId: string;
  field: 'cost' | 'region';
  okso?: string;
  raw: number | string;
  reason: string;
}

export interface Model {
  snapshotDate: string;
  campaignYear: string;
  orgs: Org[];
  foreignOrgs: Org[]; // зарубежные филиалы: без страниц, упоминаются у головных
  cities: City[];
  regions: Region[];
  directions: Direction[];
  ugsCodes: string[];
  sanitation: SanitationEntry[];
}
