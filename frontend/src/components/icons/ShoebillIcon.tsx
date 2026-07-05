interface Props {
  size?: number;
  className?: string;
}

// Side-profile silhouette: large rounded head on the left, massive flat bill
// extending right, hooked tip. Eye rendered as an evenodd cutout.
export function ShoebillIcon({ size = 24, className = "" }: Props) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 -2 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="
          M8 2
          C4 2 1 5 1 10
          C1 15 4 18 8 18
          C11 18 14 16 15 14
          L21 12 L22 10.5 L21 8.5
          L15 8
          C14 5 11 2 8 2
          Z
          M9.2 9
          A1.2 1.2 0 1 1 6.8 9
          A1.2 1.2 0 1 1 9.2 9
          Z
        "
      />
    </svg>
  );
}
