<script lang="ts">
  import Form from "$lib/components/Form.svelte";
  import UsernameField from "$lib/components/UsernameField.svelte";
  import EmailField from "$lib/components/EmailField.svelte";
  import PasswordField from "$lib/components/PasswordField.svelte";
  import ConfirmPasswordField from "$lib/components/ConfirmPasswordField.svelte";
  import RegisterButton from "$lib/components/RegisterButton.svelte";

  let username: string = "";
  let email: string = "";
  let password: string = "";
  let confirmPassword: string = "";
  let errorMessage: string = "";

  const handleSubmit = async () => {};
</script>

<Form title="Register" {errorMessage} submitHandler={handleSubmit}>
  <UsernameField bind:value={username} />
  <EmailField bind:value={email} />
  <PasswordField bind:value={password} />
  <ConfirmPasswordField bind:value={confirmPassword} />
  <RegisterButton />
</Form>
