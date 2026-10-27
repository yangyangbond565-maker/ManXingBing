import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const replaceNodeEnv = {
  name: 'replace-node-env',
  enforce: 'pre',
  transform(code) {
    if (code.includes('process.env.NODE_ENV')) {
      return code.replaceAll('process.env.NODE_ENV', JSON.stringify('production'))
    }
  }
}

export default defineConfig({
  plugins: [replaceNodeEnv, vue()],
  esbuild: false,
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: { '/api': { target: 'http://127.0.0.1:8080', changeOrigin: true } }
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
    proxy: { '/api': { target: 'http://127.0.0.1:8080', changeOrigin: true } }
  },
  build: { outDir: 'dist', sourcemap: false, minify: false, chunkSizeWarningLimit: 1200 }
})
