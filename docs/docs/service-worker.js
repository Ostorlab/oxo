importScripts("https://storage.googleapis.com/workbox-cdn/releases/4.3.1/workbox-sw.js");
// service-worker.js

// workbox.core.setCacheNameDetails({ prefix: 'd4' })
// //Change this value every time before you build
// const LATEST_VERSION = 'v0.0'
// self.addEventListener('activate', (event) => {
//   console.log(`%c ${LATEST_VERSION} `, 'background: #ddd; color: #0000ff')
//   if (caches) {
//     caches.keys().then((arr) => {
//       arr.forEach((key) => {
//         if (key.indexOf('d4-precache') < -1) {
//           caches.delete(key).then(() => console.log(`%c Cleared ${key}`, 'background: #333; color: #ff0000'))
//         } else {
//           caches.open(key).then((cache) => {
//             cache.match('version').then((res) => {
//               if (!res) {
//                 cache.put('version', new Response(LATEST_VERSION, { status: 200, statusText: LATEST_VERSION }))
//               } else if (res.statusText !== LATEST_VERSION) {
//                 caches.delete(key).then(() => console.log(`%c Cleared Cache ${LATEST_VERSION}`, 'background: #333; color: #ff0000'))
//               } else console.log(`%c Great you have the latest version ${LATEST_VERSION}`, 'background: #333; color: #00ff00')
//             })
//           })
//         }
//       })
//     })
//   }
// })

self.addEventListener('activate', function (event) {
      event.waitUntil(
        caches.keys().then(function (cacheNames) {
          console.info('deleting cache')
          return Promise.all(
            cacheNames
              .filter(function (cacheName) {
                return true
              })
              .map(function (cacheName) {
                return caches.delete(cacheName)
              }),
          )
        }),
      )
    })

console.info('From worker')
// workbox.skipWaiting()
// workbox.clientsClaim()
//
// self.__precacheManifest = [].concat(self.__precacheManifest || [])
// workbox.precaching.suppressWarnings()
// workbox.precaching.precacheAndRoute(self.__precacheManifest, {})