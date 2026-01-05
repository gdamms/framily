<script lang="ts">
  import { goto } from '$app/navigation';
  import Form from "$lib/components/Form.svelte";
  import EmailField from "$lib/components/EmailField.svelte";
  import PasswordField from "$lib/components/PasswordField.svelte";
  import LoginButton from "$lib/components/LoginButton.svelte";
  import { api } from "$lib/api";
  import { authStore } from "$lib/stores/auth";

  let email: string = "";
  let password: string = "";
  let errorMessage: string = "";
  let isLoading: boolean = false;

  const handleSubmit = async () => {
    errorMessage = "";

    // Validation
    if (!email || !password) {
      errorMessage = "Email and password are required";
      return;
    }

    isLoading = true;

    try {
      const response = await api.auth.login(email, password);
      authStore.setToken(response.access_token);
      await goto("/");
    } catch (error: any) {
      errorMessage = error.message || "Login failed";
    } finally {
      isLoading = false;
    }
  };
</script>

<Form title="Login" {errorMessage} submitHandler={handleSubmit}>
  <EmailField bind:value={email} />
  <PasswordField bind:value={password} />
  <LoginButton />
</Form>
