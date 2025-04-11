// components/DestinationTable.vue
<template>
  <div class="max-h-[400px] overflow-y-auto">
    <table class="table-auto w-full border-collapse border">
      <thead>
        <tr class="bg-gray-200">
          <th class="border px-4 py-2">Name</th>
          <th class="border px-4 py-2">Official Name</th>
          <th class="border px-4 py-2">X</th>
          <th class="border px-4 py-2">Y</th>
          <th class="border px-4 py-2">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="dest in destinations" :key="dest.id">
          <td class="border px-4 py-2">{{ dest.name }}</td>
          <td class="border px-4 py-2">
            <span v-if="!editIdSet.has(dest.id)">{{ dest.official_name ?? '-' }}</span>
            <input v-else v-model="editValues[dest.id]" class="border px-2 py-1" />
          </td>
          <td class="border px-4 py-2">{{ dest.x }}</td>
          <td class="border px-4 py-2">{{ dest.y }}</td>
          <td class="border px-4 py-2">
            <button @click="toggleEdit(dest)" class="bg-blue-500 text-white px-2 py-1 rounded">
              <font-awesome-icon :icon="['fas', editIdSet.has(dest.id) ? 'save' : 'pen']" />
            </button>
            <button @click="confirmDelete(dest.name)" class="bg-red-500 text-white px-2 py-1 rounded ml-2">
              <font-awesome-icon :icon="['fas', 'trash']" />
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
export default {
  components: {
    FontAwesomeIcon
  },
  data() {
    return {
      destinations: [],
      editIdSet: new Set(),
      editValues: {},
    };
  },
  methods: {
    async fetchDestinations() {
      const res = await fetch('/destination');
      const data = await res.json();
      this.destinations = data.destinations;
    },
    toggleEdit(dest) {
      if (this.editIdSet.has(dest.id)) {
        this.updateOfficialName(dest.id, this.editValues[dest.id]);
        this.editIdSet.delete(dest.id);
      } else {
        this.editValues[dest.id] = dest.official_name || '';
        this.editIdSet.add(dest.id);
      }
    },
    async updateOfficialName(id, newName) {
      await fetch(`/update/destination/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ official_name: newName })
      });
      this.$emit('updated', 'Updated official name');
      this.fetchDestinations();
    },
    confirmDelete(name) {
      if (confirm(`Are you sure you want to delete ${name}?`)) {
        this.deleteDestination(name);
      }
    },
    async deleteDestination(name) {
      await fetch('/destination', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      });
      this.$emit('updated', 'Deleted destination');
      this.fetchDestinations();
    }
  },
  mounted() {
    this.fetchDestinations();
  }
};
</script>