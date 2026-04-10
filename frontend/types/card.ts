// ─── Coordinate types ────────────────────────────────────────
export interface Coords {
  top: number;
  left: number;
  width: number;
  height: number;
}

export interface Padding {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

// ─── Component style ─────────────────────────────────────────
export type BackgroundType = "color" | "image" | "gradient";
export type TextAlign = "left" | "center" | "right" | "justify";
export type TextTransform = "none" | "uppercase" | "lowercase" | "capitalize";
export type TextDecoration = "none" | "underline" | "line-through";

export interface ComponentStyle {
  fontFamily?: string;
  fontWeight?: string;
  fontStyle?: string;
  fontSize?: number;
  color?: string;
  textAlign?: TextAlign;
  letterSpacing?: number;
  textTransform?: TextTransform;
  textDecoration?: TextDecoration;
  opacity?: number;
  backgroundColor?: string;
  backgroundType?: BackgroundType;
  backgroundValue?: string;
  borderRadius?: number;
  padding?: Padding;
}

// ─── Value source ────────────────────────────────────────────
export type ValueSourceType = "ai_extracted" | "user_input" | "static";

export interface ValueSource {
  type: ValueSourceType;
  field?: string;
  extractedFrom?: string;
}

// ─── Component ───────────────────────────────────────────────
export type ComponentTypeEnum =
  | "logo"
  | "fullName"
  | "position"
  | "organization_name"
  | "email"
  | "phoneNumber"
  | "website"
  | "cardBackground"
  | "fbLink"
  | "liLink"
  | "igLink";

export type CardComponentType = "role_content" | "design_element";
export type CardSide = "front" | "back";

export interface CardComponent {
  id: string;
  type: CardComponentType;
  cardSide: CardSide;
  componentType: ComponentTypeEnum;
  visible: boolean;
  zIndex: number;
  hCoords: Coords;
  vCoords: Coords;
  componentStyle: ComponentStyle;
  valueSource: ValueSource;
  fallbackText: string;
}

// ─── Card metadata ───────────────────────────────────────────
export interface CardMetadata {
  templateId: string;
  generatedBy: string;
}

export interface FinalCardJSON {
  cardMetadata: CardMetadata;
  components: CardComponent[];
}

// ─── API types ───────────────────────────────────────────────
export interface UserData {
  fullName: string;
  position: string;
  email: string;
  phoneNumber: string;
}

export interface GenerateRequest {
  url: string;
  user_data: UserData;
}

export interface GenerateResponse {
  success: boolean;
  final_card_json: FinalCardJSON;
  template_id: string;
  backend_state?: Record<string, any>;
  error: string | null;
}
