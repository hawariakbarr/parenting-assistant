module.exports = {
  apps: [
    {
      name: 'openclaw-18789',
      script: '/usr/lib/node_modules/openclaw/openclaw.mjs',
      interpreter: '/usr/bin/node',
      cwd: '/root/.openclaw',
      env: {
        NODE_ENV: 'production',
      },
      restart_delay: 3000,
      max_restarts: 10,
      watch: false,
    },
  ],
}
