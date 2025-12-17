import type { RefObject } from 'react';

/**
 * Export a chart element to PNG
 * Works with Recharts SVG elements
 */
export async function exportChartToPNG(
  chartRef: RefObject<HTMLDivElement | null>,
  filename: string = 'chart'
): Promise<boolean> {
  if (!chartRef.current) {
    console.warn('Chart reference is null');
    return false;
  }

  const svgElement = chartRef.current.querySelector('svg');
  if (!svgElement) {
    console.warn('No SVG element found in chart container');
    return false;
  }

  try {
    // Clone SVG to avoid modifying the original
    const clonedSvg = svgElement.cloneNode(true) as SVGSVGElement;

    // Get computed styles and dimensions
    const bbox = svgElement.getBoundingClientRect();
    const width = bbox.width;
    const height = bbox.height;

    // Set explicit dimensions
    clonedSvg.setAttribute('width', String(width));
    clonedSvg.setAttribute('height', String(height));

    // Add white background for PNG
    const background = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    background.setAttribute('width', '100%');
    background.setAttribute('height', '100%');
    background.setAttribute('fill', 'white');
    clonedSvg.insertBefore(background, clonedSvg.firstChild);

    // Convert SVG to data URL
    const svgData = new XMLSerializer().serializeToString(clonedSvg);
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const svgUrl = URL.createObjectURL(svgBlob);

    // Create canvas and draw SVG
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      throw new Error('Could not get canvas context');
    }

    // Use higher resolution for better quality
    const scale = 2;
    canvas.width = width * scale;
    canvas.height = height * scale;
    ctx.scale(scale, scale);

    // Load SVG as image
    const img = new Image();

    return new Promise((resolve) => {
      img.onload = () => {
        ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(svgUrl);

        // Convert to PNG and download
        canvas.toBlob((blob) => {
          if (blob) {
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.download = `${filename}.png`;
            link.href = url;
            link.click();
            URL.revokeObjectURL(url);
            resolve(true);
          } else {
            resolve(false);
          }
        }, 'image/png');
      };

      img.onerror = () => {
        URL.revokeObjectURL(svgUrl);
        console.error('Failed to load SVG as image');
        resolve(false);
      };

      img.src = svgUrl;
    });
  } catch (error) {
    console.error('Error exporting chart:', error);
    return false;
  }
}

/**
 * Export a chart element to SVG file
 */
export function exportChartToSVG(
  chartRef: RefObject<HTMLDivElement | null>,
  filename: string = 'chart'
): boolean {
  if (!chartRef.current) {
    console.warn('Chart reference is null');
    return false;
  }

  const svgElement = chartRef.current.querySelector('svg');
  if (!svgElement) {
    console.warn('No SVG element found in chart container');
    return false;
  }

  try {
    // Clone and prepare SVG
    const clonedSvg = svgElement.cloneNode(true) as SVGSVGElement;
    const bbox = svgElement.getBoundingClientRect();

    clonedSvg.setAttribute('width', String(bbox.width));
    clonedSvg.setAttribute('height', String(bbox.height));
    clonedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

    // Serialize and download
    const svgData = new XMLSerializer().serializeToString(clonedSvg);
    const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.download = `${filename}.svg`;
    link.href = url;
    link.click();

    URL.revokeObjectURL(url);
    return true;
  } catch (error) {
    console.error('Error exporting SVG:', error);
    return false;
  }
}

/**
 * Copy chart as PNG to clipboard
 */
export async function copyChartToClipboard(
  chartRef: RefObject<HTMLDivElement | null>
): Promise<boolean> {
  if (!chartRef.current) {
    return false;
  }

  const svgElement = chartRef.current.querySelector('svg');
  if (!svgElement) {
    return false;
  }

  try {
    const clonedSvg = svgElement.cloneNode(true) as SVGSVGElement;
    const bbox = svgElement.getBoundingClientRect();

    clonedSvg.setAttribute('width', String(bbox.width));
    clonedSvg.setAttribute('height', String(bbox.height));

    const background = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    background.setAttribute('width', '100%');
    background.setAttribute('height', '100%');
    background.setAttribute('fill', 'white');
    clonedSvg.insertBefore(background, clonedSvg.firstChild);

    const svgData = new XMLSerializer().serializeToString(clonedSvg);
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const svgUrl = URL.createObjectURL(svgBlob);

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return false;

    const scale = 2;
    canvas.width = bbox.width * scale;
    canvas.height = bbox.height * scale;
    ctx.scale(scale, scale);

    const img = new Image();

    return new Promise((resolve) => {
      img.onload = async () => {
        ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(svgUrl);

        canvas.toBlob(async (blob) => {
          if (blob) {
            try {
              await navigator.clipboard.write([
                new ClipboardItem({ 'image/png': blob })
              ]);
              resolve(true);
            } catch {
              resolve(false);
            }
          } else {
            resolve(false);
          }
        }, 'image/png');
      };

      img.onerror = () => {
        URL.revokeObjectURL(svgUrl);
        resolve(false);
      };

      img.src = svgUrl;
    });
  } catch {
    return false;
  }
}
