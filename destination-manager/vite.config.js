import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import rollupNodePolyFill from 'rollup-plugin-polyfill-node';

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/destination': {
        target: 'http://localhost:5055',
        changeOrigin: true,
      },
      '/update': {
        target: 'http://localhost:5055',
        changeOrigin: true,
      }
    }
  },
  define: {
    'process.env': {},
  },
  resolve: {
    alias: {
      crypto: 'crypto-browserify',
      stream: 'stream-browserify',
    },
  },
  optimizeDeps: {
    include: ['crypto-browserify'],
  },
  build: {
    rollupOptions: {
      plugins: [rollupNodePolyFill()],
    },
  },
});
