// components/Notification.vue
<template>
  <div class="fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded shadow-lg z-50">
    {{ message }}
  </div>
</template>

<script>
export default {
  props: ['message']
};
</script>