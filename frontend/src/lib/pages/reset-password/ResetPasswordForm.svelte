<script lang="ts">
  import Form from "$lib/ui/form/Form.svelte";
  import PasswordField from "$lib/ui/form/PasswordField.svelte";
  import ConfirmPasswordField from "$lib/ui/form/ConfirmPasswordField.svelte";
  import Button from "$lib/ui/Button.svelte";
  import { api } from "$lib/api/index";
  import { authView, resetToken } from "$lib/app";

  let password: string = "";
  let confirmPassword: string = "";
  let errorMessage: string = "";
  let isDone: boolean = false;
  let isLoading: boolean = false;

  const handleSubmit = async () => {
    errorMessage = "";

    const token = $resetToken;
    if (!token) {
      errorMessage = "This reset link is invalid or has expired";
      return;
    }

    if (!password || !confirmPassword) {
      errorMessage = "All fields are required";
      return;
    }

    if (password !== confirmPassword) {
      errorMessage = "Passwords do not match";
      return;
    }

    if (password.length < 8) {
      errorMessage = "Password must be at least 8 characters";
      return;
    }

    isLoading = true;

    try {
      await api.auth.resetPassword(token, password);
      resetToken.set(null);
      isDone = true;
    } catch (error: any) {
      errorMessage = error.message || "Password reset failed";
    } finally {
      isLoading = false;
    }
  };

  const backToLogin = () => {
    resetToken.set(null);
    authView.set("login");
  };
</script>

<Form title="Reset password" {errorMessage} submitHandler={handleSubmit}>
  {#if isDone}
    <p class="success">Your password has been reset. You can now log in with it.</p>
    <Button type="button" onclick={backToLogin}>Go to login</Button>
  {:else}
    <PasswordField bind:value={password} placeholder="New password" />
    <ConfirmPasswordField bind:value={confirmPassword} />
    <Button type="submit" disabled={isLoading}>{isLoading ? "Saving..." : "Set new password"}</Button>
    <p class="login-link">
      <button type="button" class="link-button" onclick={backToLogin}>
        Back to login
      </button>
    </p>
  {/if}
</Form>

<style>
  .success {
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
