<script lang="ts">
  import Form from "$lib/components/Form.svelte";
  import UsernameField from "$lib/components/UsernameField.svelte";
  import PasswordField from "$lib/components/PasswordField.svelte";
  import LoginButton from "$lib/components/LoginButton.svelte";

  let username: string = "";
  let password: string = "";
  let errorMessage: string = "";

  const handleSubmit = async () => {};
</script>

<Form title="Login" {errorMessage} submitHandler={handleSubmit}>
  <UsernameField bind:value={username} />
  <PasswordField bind:value={password} />
  <LoginButton />
</Form>
