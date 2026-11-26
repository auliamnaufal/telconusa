// Matriks menu per role (spec bagian 1.2 dan 10). Server tetap menjadi penentu hak akses.
export interface NavItem {
  href: string;
  label: string;
  roles: string[];
}

const READ = ["DIRECTOR", "SCM_MANAGER", "WAREHOUSE_STAFF", "PROCUREMENT_STAFF"];

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Dashboard", roles: READ },
  { href: "/stock", label: "Stok", roles: READ },
  { href: "/stock-requests", label: "Permintaan Barang", roles: ["DIRECTOR", "SCM_MANAGER", "WAREHOUSE_STAFF"] },
  // Staf gudang membuka Pengadaan untuk mencatat penerimaan barang; FINANCE_MANAGER untuk menyetujui PO.
  { href: "/procurement", label: "Pengadaan", roles: [...READ, "FINANCE_MANAGER"] },
  { href: "/assets", label: "Aset ONT", roles: ["DIRECTOR", "SCM_MANAGER", "WAREHOUSE_STAFF"] },
  { href: "/catalog", label: "Katalog", roles: READ },
  { href: "/audit", label: "Audit", roles: ["DIRECTOR", "SCM_MANAGER"] },
];

export function navFor(role: string | undefined): NavItem[] {
  if (!role) return [];
  return NAV_ITEMS.filter((item) => item.roles.includes(role));
}

function matches(href: string, pathname: string): boolean {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

export function canAccess(role: string | undefined, pathname: string): boolean {
  return navFor(role).some((item) => matches(item.href, pathname));
}

export function homeFor(role: string | undefined): string {
  return navFor(role)[0]?.href ?? "/login";
}

export function isActive(href: string, pathname: string): boolean {
  return matches(href, pathname);
}
