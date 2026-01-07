import { useEffect, useRef } from 'react';

export function BackgroundEffects() {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const mouseRef = useRef({ x: 0, y: 0 });

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let width = canvas.width = window.innerWidth;
        let height = canvas.height = window.innerHeight;

        const gridSize = 40; // Pixel size of grid squares
        const spotlightRadius = 400; // Radius of the spotlight

        const handleMouseMove = (e: MouseEvent) => {
            mouseRef.current = { x: e.clientX, y: e.clientY };
        };

        const animate = () => {
            ctx.fillStyle = '#000000'; // Pure Black
            ctx.fillRect(0, 0, width, height);

            // We want to draw the grid ONLY where the spotlight is
            // But for performance, we can draw the grid with a radial alpha mask based on distance from mouse

            ctx.strokeStyle = '#333333'; // Dark Grey lines
            ctx.lineWidth = 1;
            ctx.beginPath();

            // Optimize: Only draw lines near the mouse? 
            // Or draw all lines but set strokeStyle to fade out?
            // Better approach for "Spotlight" effect:

            // 1. Draw faint base grid (optional, maybe barely visible)
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
            for (let x = 0; x <= width; x += gridSize) {
                ctx.moveTo(x, 0);
                ctx.lineTo(x, height);
            }
            for (let y = 0; y <= height; y += gridSize) {
                ctx.moveTo(0, y);
                ctx.lineTo(width, y);
            }
            ctx.stroke();

            // 2. Draw Spotlight Grid (Brighter)
            const { x: mx, y: my } = mouseRef.current;

            // Create a radial gradient for the mask/lighting
            const gradient = ctx.createRadialGradient(mx, my, 0, mx, my, spotlightRadius);
            gradient.addColorStop(0, 'rgba(255, 255, 255, 0.15)');
            gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');

            // We can't easily apply gradient to strokes directly in a performant way for thousands of lines if we stroke individual segments.
            // TRICK: Draw the gridlines using the gradient as strokeStyle? 
            // Actually, standard composite operation "lighter" or just overlaying might work.

            // Let's try drawing valid segments within range.

            ctx.beginPath();
            ctx.strokeStyle = gradient;
            // Note: Gradient on stroke applies relative to canvas coordinates if created that way.

            // Optimization: Only loop through grid lines within the spotlight radius
            const startX = Math.floor((mx - spotlightRadius) / gridSize) * gridSize;
            const endX = Math.ceil((mx + spotlightRadius) / gridSize) * gridSize;
            const startY = Math.floor((my - spotlightRadius) / gridSize) * gridSize;
            const endY = Math.ceil((my + spotlightRadius) / gridSize) * gridSize;

            // Vertical lines
            for (let x = startX; x <= endX; x += gridSize) {
                if (x < 0 || x > width) continue;
                ctx.moveTo(x, Math.max(0, my - spotlightRadius));
                ctx.lineTo(x, Math.min(height, my + spotlightRadius));
            }

            // Horizontal lines
            for (let y = startY; y <= endY; y += gridSize) {
                if (y < 0 || y > height) continue;
                ctx.moveTo(Math.max(0, mx - spotlightRadius), y);
                ctx.lineTo(Math.min(width, mx + spotlightRadius), y);
            }
            ctx.stroke();

            requestAnimationFrame(animate);
        };

        const handleResize = () => {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        };

        window.addEventListener('resize', handleResize);
        window.addEventListener('mousemove', handleMouseMove);
        const animationId = requestAnimationFrame(animate);

        return () => {
            window.removeEventListener('resize', handleResize);
            window.removeEventListener('mousemove', handleMouseMove);
            cancelAnimationFrame(animationId);
        };
    }, []);

    return (
        <div className="fixed inset-0 pointer-events-none overflow-hidden z-0 bg-black">
            <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />
        </div>
    );
}
