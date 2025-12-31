'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Center, Loader, Text, Stack } from '@mantine/core';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/submit');
  }, [router]);

  return (
    <Center h="80vh">
      <Stack align="center" gap="md">
        <Loader color="fonBlue" size="lg" />
        <Text c="dimmed">Redirecting to Submit Jobs...</Text>
      </Stack>
    </Center>
  );
}
