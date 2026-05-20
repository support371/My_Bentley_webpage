import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#050505',
        foreground: '#fafafa',
        card: '#141414',
        'card-foreground': '#fafafa',
        primary: '#3b82f6',
        'primary-foreground': '#ffffff',
        secondary: '#f5f5f5',
        'secondary-foreground': '#1a1a2e',
        destructive: '#ff4444',
        'destructive-foreground': '#ffffff',
        muted: '#666666',
        'muted-foreground': '#f5f5f5',
        accent: '#3b82f6',
        'accent-foreground': '#ffffff',
        border: '#333333',
        input: '#1a1a1a',
        ring: '#3b82f6',
      },
      borderRadius: {
        lg: '0.5rem',
        md: '0.375rem',
        sm: '0.25rem',
      },
    },
  },
  plugins: [],
}

export default config
