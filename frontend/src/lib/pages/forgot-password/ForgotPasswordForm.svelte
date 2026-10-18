<script lang="ts">
  import Form from "$lib/ui/form/Form.svelte";
  import EmailField from "$lib/ui/form/EmailField.svelte";
  import Button from "$lib/ui/Button.svelte";
  import { api } from "$lib/api/index";
  import { authView } from "$lib/app";

  let email: string = "";
  let errorMessage: string = "";
  let successMessage: string = "";
  let isLoading: boolean = false;

  const handleSubmit = async () => {
    errorMessage = "";
    successMessage = "";

    if (!email) {
      errorMessage = "Email is required";
      return;
    }

    isLoading = true;

    try {
      const response = await api.auth.forgotPassword(email);
      successMessage = response.message;
    } catch (error: any) {
      errorMessage = error.message || "Could not send reset email";
    } finally {
      isLoading = false;
    }
  };
</script>

<Form title="Forgot password" {errorMessage} submitHandler={handleSubmit}>
  <p class="hint">Enter your account's email and we'll send you a link to reset your password.</p>
  <EmailField bind:value={email} />
  <Button type="submit" disabled={isLoading}>{isLoading ? "Sending..." : "Send reset link"}</Button>
  {#if successMessage}
    <p class="success">{successMessage}</p>
  {/if}
  <p class="login-link">
    <button type="button" class="link-button" onclick={() => authView.set("login")}>
      Back to login
    </button>
  </p>
</Form>

<style>
  .hint {
    margin: 0;
    font-size: 0.9rem;
  }

  .success {
    color: var(--color-success);
    text-align: center;
    margin: 0;
  }

  .login-link {
    text-align: center;
    margin-top: 1rem;
    font-size: 0.9rem;
  }

  .link-button {
    background: none;
    border: none;
    padding: 0;
    font: inherit;
    color: var(--color-primary);
    text-decoration: underline;
    cursor: pointer;
  }
</style>
