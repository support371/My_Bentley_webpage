# iTwin Ops Frontend - Setup & Architecture Guide

## Overview

This frontend application is a modern Next.js 16 + React 19 SPA that replicates the iTwin Ops platform. It's designed to work with the existing FastAPI backend while providing a professional, real-time digital operations dashboard.

## Technology Stack

- **Framework**: Next.js 16 with App Router
- **UI Library**: React 19
- **Styling**: Tailwind CSS v4
- **Components**: shadcn/ui (custom implementation)
- **State Management**: Zustand
- **API Client**: Axios
- **Charts**: Recharts
- **Icons**: Lucide React

## Project Structure

```
/app                                    # Next.js App Router
├── (dashboard)/                        # Protected routes group
│   ├── dashboard/                      # Main dashboard
│   ├── projects/                       # Project management
│   │   ├── page.tsx                    # Projects list
│   │   └── [id]/page.tsx               # Project detail
│   ├── imodels/                        # iModel management
│   ├── itwins/                         # iTwin management
│   ├── events/                         # Event log
│   ├── settings/                       # User settings
│   └── layout.tsx                      # Dashboard layout with sidebar
├── auth/
│   └── login/page.tsx                  # Login page
├── page.tsx                            # Root redirect
├── layout.tsx                          # Root layout
└── globals.css                         # Global styles

/components
├── ui/                                 # Base UI components
│   ├── button.tsx
│   ├── input.tsx
│   ├── card.tsx
│   ├── dialog.tsx
│   └── ...
├── sidebar.tsx                         # Navigation sidebar
├── header.tsx                          # Top header
├── project-card.tsx                    # Project card component
├── stat-card.tsx                       # Statistics card
└── ...

/lib
├── api.ts                              # API client with endpoints
├── store.ts                            # Zustand stores (auth, UI)
└── utils.ts                            # Utility functions

/public                                 # Static assets
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm or pnpm

### Installation

```bash
cd /vercel/share/v0-project

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
npm start
```

The dev server will start on `http://localhost:3000`

## Configuration

### Environment Variables

Create a `.env.local` file in the project root:

```env
NEXT_PUBLIC_API_URL=http://localhost:5000/api
NEXT_PUBLIC_APP_NAME=iTwin Ops
NEXT_PUBLIC_ENVIRONMENT=development
```

### API Configuration

The API client is configured in `/lib/api.ts`. Update the baseURL to match your FastAPI backend:

```typescript
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api',
})
```

### Tailwind CSS Configuration

Colors and theme are defined in `tailwind.config.ts`:

```typescript
colors: {
  background: '#050505',
  foreground: '#fafafa',
  primary: '#3b82f6',
  // ... more colors
}
```

## Features Implemented

### ✅ Phase 1: Frontend Architecture
- [x] Next.js 16 setup with TypeScript
- [x] Tailwind CSS v4 with custom theme
- [x] shadcn/ui component library
- [x] Authentication flow structure
- [x] API client with Axios
- [x] State management with Zustand
- [x] Responsive layout with sidebar

### ✅ Phase 2: Dashboard & Core Features
- [x] Main dashboard with KPIs and charts
- [x] Project management (list, detail, create)
- [x] Event logging and filtering
- [x] iModel management with sync status
- [x] Real-time data visualization
- [x] Team member management
- [x] Project detail page with progress tracking

### 🔄 Phase 3: Advanced Features (Pending)
- [ ] Admin panel with user/team management
- [ ] Role-based access control (RBAC)
- [ ] Real-time WebSocket updates
- [ ] Notification system
- [ ] Advanced search and filtering
- [ ] Custom reporting

### 🔄 Phase 4: Backend Integration (Pending)
- [ ] Google OAuth implementation
- [ ] JWT token management
- [ ] WebSocket support for real-time
- [ ] CORS configuration
- [ ] API route enhancements

## Authentication

### Current Implementation

The auth system uses Zustand for state management and stores tokens in localStorage:

```typescript
// Login flow
const { setUser, setToken } = useAuthStore()
setToken(access_token)
setUser(user)
localStorage.setItem('access_token', access_token)
```

### Protected Routes

The dashboard layout checks authentication:

```typescript
// app/(dashboard)/layout.tsx
const { isAuthenticated } = useAuthStore()
if (!isAuthenticated) router.push('/auth/login')
```

## API Integration

### Available Endpoints

```typescript
// Authentication
authAPI.login(email, password)
authAPI.signup(email, password, name)
authAPI.logout()
authAPI.me()

// Projects
projectsAPI.list(params)
projectsAPI.get(id)
projectsAPI.create(data)
projectsAPI.update(id, data)
projectsAPI.delete(id)

// iModels & iTwins
iModelsAPI.list(), iModelsAPI.get(), etc.
iTwinsAPI.list(), iTwinsAPI.get(), etc.

// Events & Dashboard
eventsAPI.list(), eventsAPI.get()
dashboardAPI.stats(), dashboardAPI.recentEvents()
```

## Component Usage Examples

### Using StatCard

```typescript
<StatCard
  title="Active Projects"
  value={8}
  variant="success"
  trend="up"
  trendValue="+2 this month"
  icon={Folder}
/>
```

### Using ProjectCard

```typescript
<ProjectCard
  id="1"
  name="Central Tower"
  description="Urban development"
  status="active"
  progress={75}
  team={8}
  dateModified="2024-01-15"
/>
```

## Styling Guidelines

### Color Palette

- **Background**: `#050505` (near black)
- **Foreground**: `#fafafa` (near white)
- **Primary**: `#3b82f6` (blue)
- **Success**: `#22c55e` (green)
- **Warning**: `#f59e0b` (amber)
- **Danger**: `#ef4444` (red)

### Responsive Breakpoints

- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px

Tailwind classes: `md:`, `lg:`, `xl:` etc.

## Performance Optimization

### Code Splitting

Routes are automatically code-split by Next.js. Components use dynamic imports when needed:

```typescript
const ExpensiveChart = dynamic(
  () => import('@/components/expensive-chart'),
  { loading: () => <div>Loading...</div> }
)
```

### Image Optimization

Use Next.js Image component:

```typescript
import Image from 'next/image'
<Image src="/logo.png" width={40} height={40} alt="Logo" />
```

### Bundle Analysis

Check bundle size:

```bash
npm run build
```

## Debugging

### Console Logging

Use `[v0]` prefix for debugging:

```typescript
console.log('[v0] State:', authStore.getState())
```

### Browser DevTools

- **React DevTools**: Inspect component hierarchy and state
- **Redux DevTools**: Monitor Zustand state changes
- **Network Tab**: Monitor API calls and responses

## Deployment

### Vercel Deployment

The project is configured for easy Vercel deployment:

```bash
npm install -g vercel
vercel
```

### Docker Deployment

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY . .
RUN npm install && npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## Contributing Guidelines

1. **Component Development**: Place new components in `/components`
2. **Page Development**: Create pages in `/app` using the App Router
3. **Styling**: Use Tailwind CSS classes, avoid inline styles
4. **API Calls**: Use the client in `/lib/api.ts`
5. **State**: Use Zustand stores in `/lib/store.ts`

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
# Or use a different port
npm run dev -- -p 3001
```

### Build Errors

```bash
# Clear cache and rebuild
rm -rf .next
npm run build
```

### API Connection Issues

1. Verify FastAPI backend is running on port 5000
2. Check `NEXT_PUBLIC_API_URL` in `.env.local`
3. Check CORS configuration in FastAPI

## Next Steps

1. **Integrate Backend**: Connect to existing FastAPI routes
2. **Implement Auth**: Add OAuth and JWT token handling
3. **Add Real-time**: WebSocket integration for live updates
4. **User Testing**: Gather feedback and iterate on UX
5. **Performance**: Monitor and optimize metrics

## Support & Resources

- [Next.js Docs](https://nextjs.org/docs)
- [React 19](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [Zustand Docs](https://github.com/pmndrs/zustand)

---

**Last Updated**: January 2024
**Version**: 1.0.0
