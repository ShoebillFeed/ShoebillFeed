import {
  Star, Heart, Flag, Globe, Compass, Flame, Rocket, Coffee,
  Home, Briefcase, Music, Camera, Gamepad2, Sparkles, Trophy,
  Lightbulb, Gift, GraduationCap, Mic, Rss, Layers, MapPin,
  Leaf, PawPrint,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { TAB_ICON_NAMES, type TabIconName } from "../types/tabs";

// Curated so a custom tab's icon is never confused with an icon that already
// means something specific elsewhere in the app (e.g. Bookmark = Read Later,
// TrendingUp = Impact sort). Keep in sync with backend/app/api/tabs.py.
export const TAB_ICONS: Record<TabIconName, LucideIcon> = {
  star: Star,
  heart: Heart,
  flag: Flag,
  globe: Globe,
  compass: Compass,
  flame: Flame,
  rocket: Rocket,
  coffee: Coffee,
  home: Home,
  briefcase: Briefcase,
  music: Music,
  camera: Camera,
  gamepad2: Gamepad2,
  sparkles: Sparkles,
  trophy: Trophy,
  lightbulb: Lightbulb,
  gift: Gift,
  graduationcap: GraduationCap,
  mic: Mic,
  rss: Rss,
  layers: Layers,
  mappin: MapPin,
  leaf: Leaf,
  pawprint: PawPrint,
};

export { TAB_ICON_NAMES };
export type { TabIconName };
