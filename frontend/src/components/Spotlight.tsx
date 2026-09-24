import React from 'react';
import './Spotlight.css';

export interface SpotlightProps {
  /**
   * Additional CSS class names for positioning or scaling.
   */
  className?: string;
  /**
   * Fill color for the spotlight beam ellipse.
   * Defaults to Agent JGH Gold (#F59E0B).
   */
  fill?: string;
  /**
   * Opacity for the spotlight beam.
   * Defaults to 0.16 for a subtle, executive ambience.
   */
  fillOpacity?: number | string;
  /**
   * Unique ID for the SVG filter to avoid collision when multiple spotlights exist.
   * Defaults to 'spotlight-filter'.
   */
  filterId?: string;
  /**
   * Optional inline styles for custom coordinates or transitions.
   */
  style?: React.CSSProperties;
}

/**
 * Aceternity UI Spotlight Component
 *
 * Renders an SVG-based ambient beam with Gaussian blur that illuminates
 * hero sections or card backgrounds without obstructing user interactions.
 */
export const Spotlight: React.FC<SpotlightProps> = ({
  className = '',
  fill = '#F59E0B',
  fillOpacity = 0.16,
  filterId = 'spotlight-filter',
  style = {},
}) => {
  return (
    <svg
      className={`aceternity-spotlight ${className}`}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 3787 2842"
      fill="none"
      style={style}
      aria-hidden="true"
    >
      <g filter={`url(#${filterId})`}>
        <ellipse
          cx="1924.71"
          cy="273.501"
          rx="1924.71"
          ry="273.501"
          transform="matrix(-0.822377 -0.568943 -0.568943 0.822377 3631.88 2291.09)"
          fill={fill}
          fillOpacity={fillOpacity}
        />
      </g>
      <defs>
        <filter
          id={filterId}
          x="0.860352"
          y="0.838989"
          width="3785.16"
          height="2840.26"
          filterUnits="userSpaceOnUse"
          colorInterpolationFilters="sRGB"
        >
          <feFlood floodOpacity="0" result="BackgroundImageFix" />
          <feBlend
            mode="normal"
            in="SourceGraphic"
            in2="BackgroundImageFix"
            result="shape"
          />
          <feGaussianBlur
            stdDeviation="151"
            result="effect1_foregroundBlur_1065_8"
          />
        </filter>
      </defs>
    </svg>
  );
};

export default Spotlight;
