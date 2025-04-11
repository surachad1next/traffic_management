// App.vue
<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">Destination Manager</h1>
    <Notification :message="notification" v-if="notification" />
    <DestinationTable @updated="showNotification" />
  </div>
</template>

<script>
import DestinationTable from './components/DestinationTable.vue';
import Notification from './components/Notification.vue';

export default {
  components: {
    DestinationTable,
    Notification,
  },
  data() {
    return {
      notification: '',
    };
  },
  methods: {
    showNotification(msg) {
      this.notification = msg;
      setTimeout(() => this.notification = '', 3000);
    }
  }
};
</script>

<style>
body {
  font-family: Arial, sans-serif;
}
</style>
