<!-- // components/DestinationTable.vue
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
</script> -->

<template>
  <div class="grid gap-6 p-4">
    <!-- Section 1: Add Robot -->
    <div class="bg-custom-gray p-4 rounded shadow">
      <h2 class="text-xl font-semibold mb-2 text-gray-800">Robot List(s)</h2>

      <!-- แสดงรายการหุ่นยนต์ที่มีอยู่ -->
      <div class="mb-4">
        <ul class="list-none">
          <li v-for="robot in robots" :key="robot.robot_id" class="text-gray-600">{{ robot.robot_id }}</li>
        </ul>
      </div>

      <!-- ฟอร์มเพิ่มหุ่นยนต์ -->
      <input v-model="newRobotId" placeholder="Enter Robot unique name" class="border px-2 py-1 mr-2 rounded" />
      <button @click="addRobot" class="bg-green-600 text-white px-3 py-1 rounded">Add</button>
    </div>

    <!-- Section 2: Upload .smap File -->
    <div class="bg-custom-gray p-4 rounded shadow">
      <h2 class="text-xl font-semibold mb-2 text-gray-800">Upload Map file</h2>
      <input type="file" @change="handleFileUpload" accept=".smap" class="mr-2" />
      <button @click="uploadFile" class="bg-purple-600 text-white px-3 py-1 rounded">Upload</button>
    </div>

    <!-- Section 3: Destination Table -->
    <div class="bg-custom-gray  p-4 rounded shadow max-h-[400px] overflow-y-auto table-container">
      <h2 class="text-xl font-semibold mb-4 text-gray-800">Destination Manager</h2>
      <table class="table-auto w-full border-collapse border">
        <thead>
          <tr class="bg-gray-200">
            <th class="border px-4 py-2">Name</th>
            <th class="border px-4 py-2">Official Name</th>
            <!-- <th class="border px-4 py-2">X</th>
            <th class="border px-4 py-2">Y</th> -->
            <th class="border px-4 py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="dest in destinations" :key="dest.id">
            <td class="border px-4 py-2">{{ dest.name }}</td>
            <td class="border px-4 py-2">
              <span v-if="!editIdSet.has(dest.id)">{{ dest.official_name ?? '-' }}</span>
              <input v-else v-model="editValues[dest.id]" class="border px-2 py-1 rounded" />
            </td>
            <!-- <td class="border px-4 py-2">{{ dest.x }}</td>
            <td class="border px-4 py-2">{{ dest.y }}</td> -->
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
      newRobotId: '',
      selectedFile: null,
    };
  },
  methods: {
    async fetchDestinations() {
      const res = await fetch('/destination');
      const data = await res.json();
      this.destinations = data.destinations;
    },
    async fetchRobots() {
      const res = await fetch('/robots/available');
      const data = await res.json();
      this.robots = data; // อัพเดตข้อมูลหุ่นยนต์ที่มีอยู่
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
    },
    async addRobot() {
      if (!this.newRobotId) return alert('Please enter robot_id');
      await fetch('/robots/available', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ robot_id: this.newRobotId, x: 0, y: 0, angle: 0 })
      });
      this.$emit('updated', `Added robot: ${this.newRobotId}`);
      this.newRobotId = '';
      this.fetchRobots(); // ดึงข้อมูลหุ่นยนต์ใหม่ทุกครั้งที่เพิ่ม
    },
    handleFileUpload(e) {
      this.selectedFile = e.target.files[0];
    },
    async uploadFile() {
      if (!this.selectedFile) return alert('No file selected');
      const formData = new FormData();
      formData.append('file', this.selectedFile);

      await fetch('/destination', {
        method: 'POST',
        body: formData
      });
      this.$emit('updated', 'Uploaded .smap file');
      this.selectedFile = null;
      this.fetchDestinations();
    }
  },
  mounted() {
    this.fetchDestinations();
    this.fetchRobots(); // เรียก `fetchRobots` เพื่อดึงข้อมูลหุ่นยนต์เมื่อเริ่มต้น
  }
};
</script>