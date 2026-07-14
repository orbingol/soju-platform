export interface NavItem {
  label: string;
  href: string;
  current?: boolean;
  children?: NavItem[];
}
