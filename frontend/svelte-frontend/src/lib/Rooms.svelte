<script>
  let rooms = []
    const fetching = async () => {
        let response = await fetch('http://127.0.0.1:8000/api/rooms/')
        rooms = await response.json()

    }

    fetching()

</script>

<ul>
    {#each rooms as room}
        <li>
            <p>{room.name}</p>
        </li>
    {/each}
</ul>

<style>
    ul {
        list-style: none;
    }
</style>